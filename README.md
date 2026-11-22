# URL Shortener — INF326 Tarea 2

Este repositorio contiene las implementaciones de las dos arquitecturas de la tarea.

## Integrantes

- Marco Repetto (202103059-K)

## Arquitectura 1

_Pendiente: agregar aquí la descripción, requisitos, instrucciones de ejecución y
pruebas de la Arquitectura 1._

## Arquitectura 2

Servicio LiteStar que persiste la terna `<id, hash, long_url>` en SQLite y
responde las redirecciones con HTTP 301.

### Requisitos e inicio

Los siguientes comandos se ejecutan desde el directorio `ARQ 02`.

- Python 3.11 o superior y OpenSSL.
- Cree el entorno: `python -m venv .venv && . .venv/bin/activate`.
- Instale las dependencias: `pip install -r requirements.txt`.
- Genere el certificado autofirmado: `sh scripts/gen_certs.sh`.
- Inicie el servicio: `uvicorn app.main:app --host 0.0.0.0 --port 8443 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem`.

El archivo SQLite se crea en `data/shortener.db`. Se puede cambiar mediante
`SHORTENER_DB_PATH`; la URL que se retorna se configura con `PUBLIC_BASE_URL`.

### Prueba rápida

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
