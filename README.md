# URL Shortener — INF326 Tarea 2

Este repositorio contiene las implementaciones de las dos arquitecturas de la tarea.

## Integrantes

- Marco Repetto (202103059-K)

## Arquitectura 1

El acortador expone una API HTTP con LiteStar y guarda las URL en SQLite. En cada
redirección envía un evento de acceso a un servicio independiente mediante gRPC;
ese servicio almacena los eventos en otra base SQLite. Responde con HTTP 302 y
`Cache-Control: no-store, no-cache, must-revalidate`.

### Tradeoffs para el acortador de URL

- **Ventaja: medición de accesos.** Cada solicitud que llega al acortador intenta
  registrar la URL de destino y la hora. Esto sirve si el caso de uso exige
  estadísticas de clics o auditoría de redirecciones. La redirección 302 y la
  prohibición de caché favorecen que las visitas posteriores vuelvan al servicio.
- **Ventaja: responsabilidades separadas.** El registro de accesos tiene su propio
  proceso y base de datos. Es posible modificar su lógica sin cambiar la
  persistencia de URL y asignarle recursos de forma independiente.
- **Costo: más componentes y latencia por visita.** Hay que ejecutar, conectar y
  supervisar dos procesos y dos bases de datos. Cada redirección espera una
  llamada gRPC antes de responder, por lo que la demora del registrador afecta
  directamente el tiempo de respuesta. La ausencia de caché también incrementa
  las solicitudes que debe procesar el origen.
- **Costo de comunicación.** La conexión gRPC actual no usa cifrado ni
  autenticación; conviene restringirla a una red interna o protegerla antes de
  exponerla.

Esta opción conviene cuando importa observar cada visita que llega al servidor
y se acepta operar un servicio adicional.

## Arquitectura 2

Servicio LiteStar que persiste la terna `<id, hash, long_url>` en SQLite y
responde las redirecciones con HTTP 301.

### Tradeoffs para el acortador de URL

- **Ventaja: ruta de redirección simple y rápida.** Un solo servicio consulta la
  URL y devuelve su destino, sin llamada a otro proceso. Las respuestas 301
  exitosas se guardan en la caché de LiteStar durante una hora y anuncian
  `Cache-Control: public, max-age=3600`; esto reduce consultas repetidas
  y puede reducir solicitudes al origen cuando los clientes respetan la caché.
- **Ventaja: menor costo operativo.** Un solo proceso facilita el
  despliegue y el mantenimiento de un acortador pequeño. La API valida que
  el destino sea una URL absoluta HTTP(S), limita solicitudes y ofrece `/health`.
- **Costo: cambios de destino menos inmediatos.** HTTP 301 comunica que el
  redireccionamiento es permanente. Los clientes pueden conservarlo, incluso
  más allá de la caché de una hora configurada en el servidor. Es apropiado para
  enlaces cuyo destino no cambiará; si se necesitan enlaces editables, esta
  elección complica corregir o reemplazar destinos ya publicados.
- **Costo: sin métricas por clic.** No hay servicio ni tabla de eventos de acceso.
  Además, una respuesta servida desde caché evita ejecutar la consulta de
  redirección. Esta arquitectura no satisface por sí sola un requisito de conteo
  exacto de visitas.
- **Costo de coordinación al distribuir el servicio.** La caché y el límite de
  solicitudes se configuran dentro de la aplicación; si se ejecutan varias
  instancias, sus políticas y estado tendrían que coordinarse para mantener un
  comportamiento uniforme.

Esta opción conviene cuando se priorizan enlaces permanentes, lecturas frecuentes
y simplicidad operativa, y no se requieren estadísticas de cada visita.

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

## ¿Cuándo conviene aplicar cada arquitectura?

La elección depende principalmente de si el acortador debe observar las visitas
y de si los destinos de los enlaces pueden cambiar.

| Caso de aplicación | Arquitectura conveniente | Motivo |
| --- | --- | --- |
| Campañas o enlaces internos donde interesa analizar los accesos que llegan al servicio | **Arquitectura 1** | Cada redirección intenta enviar un evento al registrador; el 302 sin caché favorece que las visitas posteriores vuelvan al servidor. |
| Enlaces cuyo destino podría cambiar o corregirse | **Arquitectura 1** | El 302 comunica una redirección temporal y evita la permanencia asociada al 301. La implementación actual no ofrece un endpoint para editar destinos; habría que añadirlo. |
| Enlaces públicos de destino estable, consultados muchas veces | **Arquitectura 2** | El 301 y la caché reducen consultas repetidas y la carga sobre el servidor. |
| Servicio pequeño que busca una puesta en marcha simple y no necesita métricas por visita | **Arquitectura 2** | Solo requiere operar el acortador y su base de datos, sin un proceso gRPC adicional. |

**Observación para un despliegue de mayor escala:** si se exigiera un conteo
exacto de clics incluso ante fallas del registrador, la Arquitectura 1
necesitaría mecanismos adicionales, como reintentos o una cola persistente. En
esta tarea, el registro de accesos permite comparar las decisiones
arquitectónicas sin exigir esa garantía adicional.
