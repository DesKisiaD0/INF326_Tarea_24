# URL Shortener — INF326 Tarea 2

Este repositorio contiene las implementaciones de las dos arquitecturas solicitadas para el acortador de URLs, utilizando **LiteStar** como framework HTTP base y **gRPC** para la analítica desacoplada.

## Integrantes

- Marco Repetto (202103059-K)
- Benjamín López (202273081-1)
- Rock Simón Dabre Valenzuela (202173077-k)

---

## 1. Arquitectura 1: Analítica Desacoplada (HTTP 302 + gRPC Log Service)

El acortador expone una API HTTPS con LiteStar y persiste la terna `<id, hash, long_url>` en SQLite. Ante cada petición de redirección:
- Emite un evento `"url hit"` (`timestamp` UTC y `url`) mediante una llamada gRPC al microservicio independiente `Log Service`.
- El servicio gRPC persiste el evento en una base SQLite dedicada (`databases/log.db`).
- Responde al cliente con código **HTTP 302 Found** y cabeceras `Cache-Control: no-store, no-cache, must-revalidate` para forzar al navegador a consultar siempre el acortador y no memorizar la redirección.

### Requisitos e Inicio (Arquitectura 1)

Los siguientes comandos se ejecutan desde el directorio de la Arquitectura 1 (`ARQ 01`):

1. **Preparar entorno virtual e instalar dependencias:**
   ```bash
   python -m venv venv
   # En Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # En Linux / macOS:
   source venv/bin/activate

litestar[standard]>=2.0.0
pybase62>=0.5.0
grpcio>=1.50.0
cryptography>=41.0.0

Generar certificados SSL autofirmados (si no existen en certs/):
BASH

python -c "from cryptography import x509; from cryptography.x509.oid import NameOID; from cryptography.hazmat.primitives import hashes, serialization; from cryptography.hazmat.primitives.asymmetric import rsa; import datetime; key = rsa.generate_private_key(65537, 2048); name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')]); cert = x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(1000).not_valid_before(datetime.datetime.utcnow()).not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)).sign(key, hashes.SHA256()); open('certs/key.pem', 'wb').write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption())); open('certs/cert.pem', 'wb').write(cert.public_bytes(serialization.Encoding.PEM))"

2. **Ejecutar los servicios (en terminales separadas con el entorno activo):**

Terminal 1 — Servidor de Logs (gRPC en puerto 50051):

python grpc_server.py

Terminal 2 — API LiteStar Shortener (HTTPS en puerto 8000):

python app.py

3. **Prueba rapida arquitectura 1**

# 1. Acortar URL original (ID base 597652313 genera hash eRgfR)
curl -k -X POST https://localhost:8000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "[https://usm.cl/informatica/postulaciones-a-postgrado/2025/magister-en-ingenieria-informatica/](https://usm.cl/informatica/postulaciones-a-postgrado/2025/magister-en-ingenieria-informatica/)"}'

# 2. Redirección y emisión de evento gRPC (conservando método GET)
curl -k -sS -D - -o /dev/null https://localhost:8000/eRgfR

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

4. **BONUS: Generación de Identificadores Únicos en Ambiente Distribuido**
En un sistema centralizado, la combinación de AUTOINCREMENT de SQLite y Base62 asegura unicidad secuencial sin colisiones. Sin embargo, al escalar horizontalmente a múltiples réplicas del acortador (múltiples nodos en paralelo), el autoincremento tradicional colisiona o se convierte en un cuello de botella de contención.

Para garantizar IDs únicos en un ambiente distribuido sin degradar la concurrencia, se pueden adoptar tres estrategias reconocidas:

# 1. Twitter Snowflake / ULID (Recomendada por rendimiento):

Se genera un entero de 64 bits compuesto de:

- 41 bits: Marca de tiempo (milisegundos transcurridos).

- 10 bits: Identificador de la máquina/nodo trabajador (worker_id).

- 12 bits: Secuencia incremental local por milisegundo.

Ventaja: Genera enteros que se codifican directamente a Base62 sin requerir llamadas de red ni sincronización entre nodos, garantizando unicidad absoluta y orden cronológico.

# 2. Asignación de Rangos por Bloques (Range Allocation vía Redis / Etcd / ZooKeeper):

- Un coordinador central entrega a cada réplica un bloque de identificadores (ejemplo: Nodo 1 reserva del 1,000,000 al 1,999,999; Nodo 2 reserva del 2,000,000 al 2,999,999).

- Cada nodo incrementa en memoria sus IDs de forma ultrarrápida. Solo contacta al coordinador central cuando agota su rango para solicitar uno nuevo.

# 3. Hashing Criptográfico Truncado con Salt/Nonce:

Se calcula un hash criptográfico de la URL junto a un timestamp (SHA-256(long_url + timestamp + worker_id)), tomando los primeros 40–50 bits para codificarlos en Base62.

Trade-off: Requiere un mecanismo de base de datos distribuida con reintentos para detectar y resolver eventuales colisiones criptográficas.