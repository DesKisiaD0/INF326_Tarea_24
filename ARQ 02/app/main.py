"""Punto de entrada ASGI de Shortener v2."""

from litestar import Litestar
from litestar.config.response_cache import ResponseCacheConfig
from litestar.middleware.rate_limit import RateLimitConfig

from app.controllers import health, redirect, repository, shorten


def create_app() -> Litestar:
    repository.initialize()
    return Litestar(
        route_handlers=[shorten, redirect, health],
        middleware=[RateLimitConfig(
            rate_limit=("minute", 60), exclude=["/health", "/schema", "/schema/"]
        ).middleware],
        # La política predeterminada guarda 2xx y 301/308, pero no 404.
        response_cache_config=ResponseCacheConfig(default_expiration=3600),
        debug=False,
    )


app = create_app()
