# Shortener v2 — INF326 Tarea 2

Implementación de la Arquitectura 2: un servicio LiteStar que persiste la terna
`<id, hash, long_url>` en SQLite y responde las redirecciones con HTTP 301.

## Integrantes

Reemplace esta sección por los nombres y roles del equipo antes de entregar.

## Requisitos e inicio

- Python 3.11 o superior y OpenSSL.
- Cree el entorno: `python -m venv .venv && . .venv/bin/activate`.
- Instale las dependencias: `pip install -r requirements.txt`.
- Genere el certificado autofirmado: `sh scripts/gen_certs.sh`.
- Inicie el servicio: `uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem`.

El archivo SQLite se crea en `data/shortener.db`. Se puede cambiar mediante
`SHORTENER_DB_PATH`; la URL que se retorna se configura con `PUBLIC_BASE_URL`.

## Prueba rápida

```sh
curl -k -X POST https://localhost:8443/shorten \
  -H 'Content-Type: application/json' \
  -d '{"long_url":"https://www.usm.cl/"}'
curl -k -sS -D - -o /dev/null https://localhost:8443/<hash-retornado>
```

La segunda llamada conserva el método GET pero descarta el cuerpo y muestra sus
cabeceras; debe responder `HTTP/1.1 301` y un encabezado `Location`. No se usa
`curl -I`, porque este envía HEAD y el endpoint de redirección es GET.
El `-k` es necesario solo porque el certificado local es autofirmado.

## Consideraciones de implementación

- El primer registro recibe `id = 597652313`; SQLite garantiza los siguientes
  identificadores autoincrementales y `pybase62` los transforma en hashes únicos.
- `RateLimitConfig` limita a 60 solicitudes por minuto por IP y responde con 429
  cuando se supera el límite.
- La ruta `GET /{short_code}` usa el caché de respuestas de LiteStar durante una
  hora. La política predeterminada incluye 301 pero no 404, por lo que las URL
  inexistentes no quedan cacheadas.
- El cliente recibe `Cache-Control: public, max-age=3600` junto al 301, por lo que
  el navegador también puede reutilizar la redirección.

La discusión requerida se encuentra en [TRADEOFFS.md](TRADEOFFS.md).
