import os
import sys
from datetime import datetime, timezone
from dataclasses import dataclass
import grpc
from litestar import Litestar, get, post, Request
from litestar.response import Redirect
from litestar.exceptions import NotFoundException

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from db_shortener import init_shortener_db, insert_url, get_long_url
from generated import logger_pb2, logger_pb2_grpc

# Conexión al servicio gRPC en localhost:50051
channel = grpc.insecure_channel("localhost:50051")
grpc_client = logger_pb2_grpc.LoggerServiceStub(channel)

def send_grpc_hit(target_url: str):
    try:
        now_utc = datetime.now(timezone.utc).isoformat()
        grpc_client.LogHit(logger_pb2.HitRequest(timestamp=now_utc, url=target_url))
    except Exception as e:
        print(f"Error comunicando con servicio gRPC: {e}", flush=True)

@dataclass
class ShortenRequest:
    url: str

@dataclass
class ShortenResponse:
    id: int
    hash: str
    short_url: str

@post("/shorten")
async def shorten(data: ShortenRequest, request: Request) -> ShortenResponse:
    url_id, url_hash = insert_url(data.url)
    base_url = str(request.base_url).rstrip("/")
    return ShortenResponse(
        id=url_id,
        hash=url_hash,
        short_url=f"{base_url}/{url_hash}"
    )

@get("/{hash:str}")
async def redirect_to_url(hash: str) -> Redirect:
    long_url = get_long_url(hash)
    if not long_url:
        raise NotFoundException(detail="URL no encontrada")

    # Enviar evento "url hit" al servicio gRPC (Arquitectura 1)
    send_grpc_hit(long_url)

    # Redirección temporal HTTP 302 sin guardar en caché
    return Redirect(
        path=long_url,
        status_code=302,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"}
    )

init_shortener_db()

app = Litestar(
    route_handlers=[shorten, redirect_to_url]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="certs/key.pem",
        ssl_certfile="certs/cert.pem",
        reload=False
    )
