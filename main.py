from fastapi import FastAPI, Query

from src.crawler import search

app = FastAPI()


@app.get("/search")
def search_endpoint(
    keyword: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
):
    results = search(keyword, page=page)
    return [item.to_dict() for item in results]

@app.get("/")
def root():
    return {
        "message": "Nalanyinyun DMHY Anime Search API",
        "version": "on development",
        "usage": "GET /search?keyword=<keyword>&page=<page_number>",
        "comment": "More function will be added in the future"
    }
