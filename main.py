import hmac
import os

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response as StarletteResponse

from src.crawler import search
from src.magnetcheck import check_health

from fastapi.middleware.cors import CORSMiddleware


DEFAULT_LOCAL_API_KEY = "local-development-only"
PRODUCTION_ENVIRONMENTS = {"prod", "production"}


def get_api_secret_key() -> str:
    api_secret_key = os.getenv("API_SECRET_KEY")
    is_production = (
        os.getenv("RENDER") is not None
        or os.getenv("ENVIRONMENT", "").lower() in PRODUCTION_ENVIRONMENTS
    )

    if is_production and not api_secret_key:
        raise RuntimeError("API_SECRET_KEY must be set in production")

    return api_secret_key or DEFAULT_LOCAL_API_KEY


API_SECRET_KEY = get_api_secret_key()
API_SECRET_KEY_BYTES = API_SECRET_KEY.encode("utf-8")


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> StarletteResponse:
        # CORS preflight requests do not include application credentials.
        if request.method == "OPTIONS":
            return await call_next(request)

        authorization = request.headers.get("Authorization", "")
        scheme, _, bearer_key = authorization.partition(" ")
        supplied_keys = [
            bearer_key if scheme.lower() == "bearer" else "",
            request.headers.get("X-API-Key", ""),
        ]

        if not any(
            supplied_key
            and hmac.compare_digest(
                supplied_key.encode("utf-8"),
                API_SECRET_KEY_BYTES,
            )
            for supplied_key in supplied_keys
        ):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API Key"},
            )

        return await call_next(request)

app = FastAPI()

app.add_middleware(
    APIKeyAuthMiddleware,
)

# Keep CORS outermost so authentication failures also receive CORS headers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://xh-anime.com",
        "https://www.xh-anime.com",
    ],
    allow_origin_regex=r"^http://(?:localhost|127\.0\.0\.1):\d+$",
    allow_methods=["GET"],
    allow_headers=["Authorization", "X-API-Key"],
)


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
