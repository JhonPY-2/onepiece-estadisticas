# specs/002-personajes-sin-tripulacion/spec.md

**Estado: implementada**

## Contexto y objetivo
El microservicio ya expone estadísticas de personajes (`/estadisticas/personajes`, `/estadisticas/resumen`, `/estadisticas/recompensas/resumen`), pero no responde a una pregunta concreta: cuántos personajes no tienen tripulación asignada. Hoy esa información solo se podría deducir mirando los datos uno por uno. El objetivo es añadir un endpoint de solo lectura que devuelva ese conteo como un único entero en el campo `cantidad`, para que un chat de IA y cualquier consumidor de la API respondan "¿cuántos personajes no tienen tripulación?" con una sola llamada y un contrato mínimo y estable. El nuevo endpoint complementa a los existentes, sin reemplazarlos ni modificarlos.

## Usuarios
- Chat de IA (conectado con n8n) que consulta el endpoint para responder preguntas sobre personajes.
- Desarrollador/consumidor de la API que inspecciona el contrato en `/docs`.

## Historias de usuario
- Como chat de IA, quiero consultar cuántos personajes no tienen tripulación asignada, para responder esa pregunta con un único dato exacto.
- Como consumidor de la API, quiero un contrato mínimo y estable (un solo campo entero), para integrarlo sin sorpresas.

## Definiciones
- **Personaje**: documento de la colección `personajes`.
- **Tripulación asignada**: en un personaje, el campo `tripulacion` con un valor presente y distinto de `null`. En los datos reales ese valor es un `ObjectId` que referencia la colección de tripulaciones (según el comentario de `tests/test_estadisticas.py` líneas 17-18), no un texto.
- **Personaje sin tripulación asignada**: documento de `personajes` cuyo campo `tripulacion` **no existe** o cuyo valor es `null`. Son las dos únicas formas de que el personaje no tenga referencia asignada.
- **La existencia del documento referenciado no cuenta**: un personaje con `tripulacion` presente (un `ObjectId`) se cuenta como **con** tripulación aunque ese `ObjectId` no corresponda a ningún documento en la colección de tripulaciones, porque la asignación existe en el propio personaje. El endpoint solo mira el campo `tripulacion` del personaje; no consulta ni resuelve la colección de tripulaciones.
- **`cantidad`**: número entero de documentos de `personajes` sin tripulación asignada.
- **Alcance de la colección**: el conteo se refiere solo a los documentos de `personajes` (la ruta del endpoint dice `personajes`), no a otras colecciones de miembros como `tripulantes`.
- **Decisión: conteo solo de `personajes`**: el conteo incluye solo la colección `personajes` y **no** `tripulantes` (decisión tomada porque la ruta es `/estadisticas/personajes/sin-tripulacion`).
- **Decisión: valor no-ObjectId en `tripulacion`**: si `tripulacion` tuviera un valor no-ObjectId (p. ej. cadena vacía `""`), cuenta como **con** tripulación (tiene valor asignado); según el comentario de `tests/test_estadisticas.py` líneas 17-18, en la base real el valor es un `ObjectId`.

## Requisitos funcionales (RF)
| ID | Requisito (en EARS) |
|---|--------------------|
| RF-1 | CUANDO un cliente envía `GET /estadisticas/personajes/sin-tripulacion`, EL SISTEMA responde con código `200`. |
| RF-2 | CUANDO un cliente envía `GET /estadisticas/personajes/sin-tripulacion`, EL SISTEMA devuelve un objeto JSON con exactamente un campo, `cantidad`, cuyo valor es un número entero, y ningún otro campo. |
| RF-3 | CUANDO se responde al endpoint, EL SISTEMA calcula `cantidad` como el número de documentos de `personajes` sin tripulación asignada. |
| RF-4 | SI un documento de `personajes` no tiene el campo `tripulacion` o lo tiene con valor `null`, ENTONCES EL SISTEMA lo cuenta en `cantidad`; SI el campo `tripulacion` tiene cualquier otro valor (incluido un `ObjectId` sin documento correspondiente en la colección de tripulaciones), ENTONCES EL SISTEMA no lo cuenta en `cantidad`. |
| RF-5 | SI la colección `personajes` está vacía, ENTONCES EL SISTEMA responde con código `200` y `cantidad` igual a `0`. |
| RF-6 | EL SISTEMA SIEMPRE devuelve `cantidad` como un número entero mayor o igual que `0` (nunca `null`, negativo ni texto). |
| RF-7 | EL SISTEMA SIEMPRE calcula `cantidad` a partir solo de los documentos de `personajes`, sin incluir documentos de otras colecciones. |

## Requisitos no funcionales (RNF)
| ID | Requisito |
|---|-----------|
| RNF-1 | El endpoint es de solo lectura: no crea, modifica ni borra datos. |
| RNF-2 | La respuesta es determinista: para el mismo estado de los datos, `cantidad` es siempre el mismo. |
| RNF-3 | El contrato (método, ruta, código de estado y forma exacta del JSON) es estable para el consumidor. |
| RNF-4 | Toda la documentación, mensajes y textos de la spec están en español. |

## Casos límite
- Colección `personajes` vacía → `200` con `cantidad` = `0` (RF-5).
- Todos los personajes tienen tripulación → `200` con `cantidad` = `0` aunque haya personajes (RF-3, RF-4).
- Ningún personaje tiene tripulación → `cantidad` igual al total de documentos de `personajes` (RF-3).
- Mezcla de personajes con y sin tripulación → `cantidad` cuenta solo los sin tripulación (RF-3, RF-4).
- Personaje sin campo `tripulacion` → se cuenta (RF-4).
- Personaje con `tripulacion` `null` → se cuenta (RF-4).
- Personaje con `tripulacion` `ObjectId` cuyo documento no existe en la colección de tripulaciones → no se cuenta: tiene asignación (RF-4).
- Personaje con `tripulacion` con valor no-ObjectId (p. ej. cadena vacía `""`) → se cuenta como con tripulación (tiene valor asignado), según la decisión de las Definiciones (RF-4).
- Un único personaje en la colección → `cantidad` es `1` si no tiene tripulación y `0` si la tiene (RF-3, RF-4).
- Método distinto de `GET` en la ruta → respondida como método no permitido, igual que los demás endpoints.
- El endpoint no acepta parámetros: cualquier parámetro de consulta no forma parte del contrato.

## Fuera de alcance
- Listar o devolver los nombres de los personajes sin tripulación (solo el conteo).
- Contar documentos de `tripulantes` u otras colecciones.
- Comprobar si la tripulación referenciada existe, corregir referencias rotas o añadir `tripulacion` a personajes que no lo tengan.
- Modificar o sustituir los endpoints existentes (`/estadisticas/personajes`, `/estadisticas/atletas`, `/estadisticas/tripulaciones`, `/estadisticas/resumen`, `/estadisticas/recompensas/resumen`).
- Filtros, paginación, autenticación o autorización.
- Escritura de datos.

## Criterios de finalización
- `GET /estadisticas/personajes/sin-tripulacion` responde `200` con un JSON que contiene exactamente el campo `cantidad` entero y ningún otro (RF-1, RF-2), verificable por test y con Chrome DevTools (solo lectura) en `/docs` y en la URL del endpoint.
- `cantidad` coincide con el número de personajes sin campo `tripulacion` o con `tripulacion` `null`, y excluye los que tienen `tripulacion` con cualquier otro valor (RF-3, RF-4, RF-7), verificable con tests con datos de prueba en la base `onepiece_test`.
- Con la colección `personajes` vacía, la respuesta es `200` con `cantidad` = `0` (RF-5).
- `cantidad` es siempre un entero `>= 0` (RF-6).
- Los endpoints existentes no cambian su comportamiento ni su contrato.
- Los tests solo usan la base `onepiece_test` y la suite completa pasa.

## Dudas abiertas
- Ninguna: las dos dudas anteriores quedaron resueltas y sus decisiones pasaron a la sección `Definiciones`.
