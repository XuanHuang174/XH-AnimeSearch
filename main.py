from fastapi import FastAPI, Query
from fastapi.responses import Response

from src.crawler import search
from src.magnetcheck import check_health

app = FastAPI()


@app.get("/search")
def search_endpoint(
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
):
    results = search(keyword, page=page)
    return [item.to_dict() for item in results]


@app.get("/health")
def health_endpoint(magnet: str = Query(..., min_length=1)):
    resp = check_health(magnet)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
    )


@app.get("/")
def root():
    return {
        "message": "Nalanyinyun DMHY Anime Search API",
        "version": "on development",
        "usage": [
            "GET /search?keyword=<keyword>&page=<page_number>",
            "GET /health?magnet=<magnet_link>",
        ],
        "comment": "More function will be added in the future",
    }
