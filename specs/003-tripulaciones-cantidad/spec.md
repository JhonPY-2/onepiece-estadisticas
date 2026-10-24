# specs/003-tripulaciones-cantidad/spec.md

**Estado: aprobada**

## Contexto y objetivo
El microservicio ya expone estadísticas de tripulaciones (`/estadisticas/tripulaciones` devuelve el total y el desglose de miembros por nombre), pero no responde de forma directa y mínima a la pregunta "¿cuántas tripulaciones hay en total?". Hoy esa cifra solo se obtiene leyendo `total_tripulaciones` dentro del objeto de la respuesta del endpoint de desglose, o contando la lista devuelta. El objetivo es añadir un endpoint de solo lectura que devuelva únicamente ese conteo como un único entero en el campo `cantidad`, con un contrato mínimo y estable, para que un chat de IA y cualquier consumidor respondan la pregunta con una sola llamada. El nuevo endpoint complementa al existente, sin reemplazarlo ni modificarlo.

El nombre de la colección de tripulaciones puede variar. El nuevo conteo debe apoyarse en el mismo mecanismo de resolución que ya usa `/estadisticas/tripulaciones`, sin repetir la lógica de resolución. Este endpoint y `/estadisticas/tripulaciones` cuentan la misma colección.

## Usuarios
- Chat de IA (conectado con n8n) que consulta el endpoint para responder preguntas sobre el número de tripulaciones.
- Desarrollador/consumidor de la API que inspecciona el contrato en `/docs`.

## Historias de usuario
- Como chat de IA, quiero consultar cuántas tripulaciones existen en total, para responder esa pregunta con un único dato exacto.
- Como consumidor de la API, quiero un contrato mínimo y estable (un solo campo entero), para integrarlo sin sorpresas.

## Definiciones
- **Colecciones candidatas**: `tripulaciones` y `tripulacions` (los dos posibles nombres de la colección de tripulaciones).
- **Colección de tripulaciones**: la colección seleccionada entre las colecciones candidatas por el mecanismo de resolución compartido con `/estadisticas/tripulaciones`; si no existe ninguna colección candidata, no hay colección de tripulaciones.
- **Tripulación**: documento perteneciente a la colección de tripulaciones (la colección seleccionada según la definición anterior).
- **`cantidad`**: número entero de documentos en la colección de tripulaciones.
- **Independencia de miembros**: el conteo cuenta **documentos de la colección de tripulaciones**, no miembros; no consulta ni tiene en cuenta `personajes` ni `tripulantes`, ni el campo `numeroMiembros`.
- **Decisión: reutilizar la resolución de nombre**: el endpoint reutiliza el mecanismo de resolución de nombre compartido con `/estadisticas/tripulaciones` (no duplicarlo), porque ambos endpoints deben contar la misma colección aunque su nombre cambie.
- **Decisión: si no existe ninguna colección candidata, 200 con cantidad = 0**: cuando no exista ninguna colección candidata, el endpoint responde `200` con `cantidad` = `0`.

## Requisitos funcionales (RF)
| ID | Requisito (en EARS) |
|---|--------------------|
| RF-1 | CUANDO un cliente envía `GET /estadisticas/tripulaciones/cantidad`, EL SISTEMA responde con código `200`. |
| RF-2 | CUANDO un cliente envía `GET /estadisticas/tripulaciones/cantidad`, EL SISTEMA devuelve un objeto JSON con exactamente un campo, `cantidad`, cuyo valor es un número entero, y ningún otro campo. |
| RF-3 | CUANDO se responde al endpoint, EL SISTEMA calcula `cantidad` como el número de documentos existentes en la colección de tripulaciones (la colección seleccionada entre las colecciones candidatas con el mecanismo compartido con `/estadisticas/tripulaciones`). |
| RF-4 | EL SISTEMA SIEMPRE calcula `cantidad` contando solo documentos de la colección de tripulaciones, sin contar ni consultar documentos de `personajes`, `tripulantes` ni otras colecciones. |
| RF-5 | SI la colección de tripulaciones está vacía, ENTONCES EL SISTEMA responde con código `200` y `cantidad` igual a `0`. |
| RF-6 | EL SISTEMA SIEMPRE devuelve `cantidad` como un número entero mayor o igual que `0` (nunca `null`, negativo ni texto). |
| RF-7 | EL SISTEMA SIEMPRE resuelve la colección de tripulaciones con el mismo mecanismo que usa `/estadisticas/tripulaciones`, de modo que este endpoint y `/estadisticas/tripulaciones` cuentan la misma colección. SI no existe ninguna colección candidata, ENTONCES EL SISTEMA responde con código `200` y `cantidad` igual a `0`. |

## Requisitos no funcionales (RNF)
| ID | Requisito |
|---|-----------|
| RNF-1 | El endpoint es de solo lectura: no crea, modifica ni borra datos. |
| RNF-2 | La respuesta es determinista: para el mismo estado de los datos, `cantidad` es siempre el mismo. |
| RNF-3 | El contrato (método, ruta, código de estado y forma exacta del JSON) es estable para el consumidor. |
| RNF-4 | El comportamiento de los endpoints existentes, en particular `/estadisticas/tripulaciones`, no cambia. |
| RNF-5 | Toda la documentación, mensajes y textos de la spec están en español. |

## Casos límite
- Colección de tripulaciones vacía → `200` con `cantidad` = `0` (RF-5).
- Ninguna colección candidata (`tripulaciones` ni `tripulacions`) existe → `200` con `cantidad` = `0` (RF-7).
- Ambas colecciones candidatas existen a la vez → se cuenta la misma colección que cuenta `/estadisticas/tripulaciones` (RF-7).
- Tripulaciones existentes pero sin miembros → `cantidad` cuenta igual cada tripulación: el conteo es de documentos de tripulaciones, no de miembros (RF-3, RF-4).
- Miembros en `personajes` o `tripulantes` cuya `tripulacion` apunta a una tripulación inexistente → no afectan a `cantidad`: el endpoint no mira miembros (RF-4).
- Cambio de nombre de la colección en la base: el endpoint cuenta la colección que exista, con cualquiera de los dos nombres (`tripulaciones` o `tripulacions`), sin presentar uno como el normal (RF-7).
- Una única tripulación → `cantidad` es `1` (RF-3).
- Un método distinto de `GET` en la ruta → responde `405` (método no permitido), igual que los demás endpoints.
- Los parámetros de consulta se ignoran, sin error (RF-1, RF-2).

## Fuera de alcance
- Modificar o sustituir los endpoints existentes, en particular `/estadisticas/tripulaciones` (que sigue devolviendo `total_tripulaciones` y `tripulaciones_por_nombre`).
- Devolver los nombres o detalles de las tripulaciones (solo el conteo).
- Contar miembros (`personajes` o `tripulantes`) o recalcular `numeroMiembros`.
- Cambiar el nombre de la colección en la base de datos o renombrarla.
- Filtros, paginación, autenticación o autorización.
- Añadir parámetros de query o de path.
- Escritura de datos.

## Criterios de finalización
- `GET /estadisticas/tripulaciones/cantidad` responde `200` con un JSON que contiene exactamente el campo `cantidad` entero y ningún otro (RF-1, RF-2), verificable por test y con Chrome DevTools (solo lectura) en `/docs` y en la URL del endpoint.
- `cantidad` coincide con el número de documentos de la colección de tripulaciones resuelta con el mecanismo compartido con `/estadisticas/tripulaciones`, sin depender de `personajes` ni `tripulantes` (RF-3, RF-4, RF-7), verificable con tests con datos de prueba en la base `onepiece_test`.
- Con la colección de tripulaciones vacía o sin ninguna colección candidata, la respuesta es `200` con `cantidad` = `0` (RF-5, RF-7).
- `cantidad` es siempre un entero `>= 0` (RF-6).
- Los endpoints existentes no cambian su comportamiento ni su contrato (RNF-4).
- Los tests solo usan la base `onepiece_test` y la suite completa pasa.

## Dudas abiertas
Ninguna
