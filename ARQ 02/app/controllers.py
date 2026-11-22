"""Rutas HTTP del acortador."""

from __future__ import annotations

import os
from urllib.parse import urlsplit

from litestar import Response, get, post
from litestar.exceptions import NotFoundException, ValidationException
from litestar.params import Body
from litestar.status_codes import HTTP_301_MOVED_PERMANENTLY

from app.db import UrlRepository
from app.models import ShortenRequest

repository = UrlRepository()
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://localhost:8443").rstrip("/")
REDIRECT_CACHE_SECONDS = 3600


def _validate_long_url(long_url: str) -> str:
    parsed = urlsplit(long_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationException(detail="long_url debe ser una URL absoluta http(s)")
    return long_url


@post("/shorten", status_code=201)
def shorten(data: ShortenRequest = Body()) -> dict[str, str]:
    """Acepta directamente el cuerpo JSON ``{"long_url": "https://..."}``."""
    url = repository.create(_validate_long_url(data.long_url))
    return {"short_url": f"{PUBLIC_BASE_URL}/{url.hash}", "hash": url.hash}


@get("/{short_code:str}", cache=REDIRECT_CACHE_SECONDS)
def redirect(short_code: str) -> Response:
    """Redirección permanente; LiteStar solo cachea los 301 exitosos."""
    url = repository.get_by_hash(short_code)
    if url is None:
        raise NotFoundException(detail="URL corta no encontrada")
    return Response(
        content=b"",
        status_code=HTTP_301_MOVED_PERMANENTLY,
        headers={
            "Location": url.long_url,
            "Cache-Control": f"public, max-age={REDIRECT_CACHE_SECONDS}",
        },
    )


@get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
