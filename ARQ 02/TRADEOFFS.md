# Trade-offs de las arquitecturas del URL shortener

## Arquitectura 1: 302 y componente de log

La redirección temporal (302) evita que el navegador reutilice la equivalencia de
forma permanente. Cada visita vuelve al acortador, que puede emitir un evento al
componente gRPC de logging. Para la USM, esto permite medir visitas, horarios,
campañas y enlaces más usados, y cambiar el destino de una URL sin esperar a que
expire el caché de los usuarios.

El costo es una petición al servicio por cada visita, más tráfico, complejidad
operacional, almacenamiento y tolerancia a fallas del servicio gRPC y su base de
datos. Una indisponibilidad del logging no debería impedir redirigir: en producción
conviene desacoplar el evento con una cola, reintentos y política de degradación.

## Arquitectura 2: 301, rate limiter y caché

Esta versión reduce latencia y carga: el navegador puede cachear el 301 y LiteStar
cachea respuestas 301 exitosas. Es apropiada para enlaces institucionales estables
(por ejemplo, páginas oficiales de admisión), donde el volumen y la disponibilidad
importan más que la analítica por visita. El rate limiter protege al proceso frente a
ráfagas o abuso básico por IP.

La contrapartida es que cambiar o revocar un destino tarda hasta el TTL en reflejarse
en cachés del servidor y navegador. Tampoco se contabilizan visitas que el navegador
resuelve desde su caché. El rate limiter y caché en memoria se reinician con el
proceso, no se comparten entre réplicas y no sustituyen defensa perimetral. Para un
despliegue multi-instancia usaría Redis compartido, límites en el proxy/WAF y una
política de invalidación para enlaces sensibles.

## Persistencia y seguridad

SQLite simplifica la tarea y conserva la unicidad del `id` en una instancia, pero no
es la opción adecuada para muchas escrituras concurrentes ni réplicas. PostgreSQL
ofrece mejor concurrencia, respaldo y operación. El certificado autofirmado cifra el
tráfico para la demostración, pero los navegadores no confían en él; producción
requiere una CA pública o corporativa y renovación automatizada.

## Bonus: unicidad distribuida

No repartiría un contador SQLite entre nodos. Se puede usar una secuencia central de
PostgreSQL, que entrega valores distintos a todas las réplicas, y luego codificar cada
valor en base62. Si se necesita independencia regional, un generador tipo Snowflake
(timestamp + id de nodo + secuencia) o UUID/ULID codificado en base62 evita
coordinación por solicitud; se debe imponer además una restricción `UNIQUE` y manejar
reintentos ante una colisión extremadamente improbable.
