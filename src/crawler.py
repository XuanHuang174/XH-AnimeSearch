from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from urllib.parse import quote, urljoin

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://share.dmhy.org"
SEARCH_PATH = "/topics/list"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


@dataclass
class TorrentItem:
    published_at: str
    category: str
    title: str
    fansub: str | None
    anime_title: str | None
    url: str
    magnet: str | None
    size: str
    seeders: str
    leechers: str
    downloads: str
    uploader: str

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


def parse_title(title: str) -> tuple[str | None, str | None]:
    """Extract fansub group and anime title from a dmhy torrent title."""
    rest = title.strip()
    groups: list[str] = []

    while rest.startswith("["):
        match = re.match(r"\[([^\]]+)\]", rest)
        if match is None:
            break
        groups.append(match.group(1))
        rest = rest[match.end() :].lstrip()

    fansub = groups[0] if groups else None
    anime = rest

    for pattern in (
        r"\s\|\s",      # batch: S01 | 01-12
        r"\s-\s\d",     # episode: - 10
        r"\s\[\d+\]",   # [38]
        r"\s\[",        # [WebRip]
        r"\s\(",        # (WEB
    ):
        match = re.search(pattern, anime)
        if match is not None:
            anime = anime[: match.start()].rstrip()

    anime = re.sub(r"\sS\d+$", "", anime).rstrip()
    return fansub, anime or None


def _build_search_url(keyword: str, page: int = 1) -> str:
    encoded = quote(keyword)
    if page <= 1:
        return f"{BASE_URL}{SEARCH_PATH}?keyword={encoded}"
    return f"{BASE_URL}{SEARCH_PATH}/page/{page}?keyword={encoded}"


def _first_text(cell) -> str:
    return next(cell.stripped_strings, "")


def _extract_title_info(title_cell) -> tuple[str, str, str | None, str | None] | None:
    title_link = title_cell.find("a", href=lambda href: href and "/topics/view/" in href)
    if title_link is None:
        return None

    title = title_link.get_text(strip=True)
    url = urljoin(BASE_URL, title_link["href"])

    tag = title_cell.find("span", class_="tag")
    tag_link = tag.find("a") if tag else None
    fansub = tag_link.get_text(strip=True) if tag_link else None

    parsed_fansub, anime_title = parse_title(title)
    if fansub is None:
        fansub = parsed_fansub

    return title, url, fansub, anime_title


def _parse_row(row) -> TorrentItem | None:
    cells = row.find_all("td")
    if len(cells) < 9:
        return None

    title_info = _extract_title_info(cells[2])
    if title_info is None:
        return None

    title, url, fansub, anime_title = title_info

    magnet_link = cells[3].find("a", class_="arrow-magnet")
    uploader_link = cells[8].find("a")

    seeders = cells[5].find("span")
    leechers = cells[6].find("span")

    return TorrentItem(
        published_at=_first_text(cells[0]),
        category=cells[1].get_text(strip=True),
        title=title,
        fansub=fansub,
        anime_title=anime_title,
        url=url,
        magnet=magnet_link["href"] if magnet_link else None,
        size=cells[4].get_text(strip=True),
        seeders=seeders.get_text(strip=True) if seeders else cells[5].get_text(strip=True),
        leechers=leechers.get_text(strip=True) if leechers else cells[6].get_text(strip=True),
        downloads=cells[7].get_text(strip=True),
        uploader=uploader_link.get_text(strip=True) if uploader_link else cells[8].get_text(strip=True),
    )


def _parse_search_page(html: str) -> list[TorrentItem]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="topic_list")
    if table is None:
        return []

    body = table.find("tbody")
    if body is None:
        return []

    items: list[TorrentItem] = []
    for row in body.find_all("tr"):
        item = _parse_row(row)
        if item is not None:
            items.append(item)
    return items


def search(
    keyword: str,
    *,
    page: int = 1,
    client: httpx.Client | None = None,
) -> list[TorrentItem]:
    """Search dmhy and return structured torrent items."""
    url = _build_search_url(keyword, page)
    owns_client = client is None
    if owns_client:
        client = httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=30)

    try:
        response = client.get(url)
        response.raise_for_status()
        return _parse_search_page(response.text)
    finally:
        if owns_client:
            client.close()


def search_all(
    keyword: str,
    *,
    max_pages: int | None = None,
    client: httpx.Client | None = None,
) -> list[TorrentItem]:
    """Fetch multiple result pages until empty or max_pages is reached."""
    owns_client = client is None
    if owns_client:
        client = httpx.Client(headers=DEFAULT_HEADERS, follow_redirects=True, timeout=30)

    all_items: list[TorrentItem] = []
    page = 1

    try:
        while True:
            if max_pages is not None and page > max_pages:
                break

            items = search(keyword, page=page, client=client)
            if not items:
                break

            all_items.extend(items)
            page += 1
    finally:
        if owns_client:
            client.close()

    return all_items


if __name__ == "__main__":
    import json

    results = search("葬送的芙莉莲")
    print(json.dumps([item.to_dict() for item in results[:3]], ensure_ascii=False, indent=2))
    print(f"\n共 {len(results)} 条结果")
