# specs/001-resumen-recompensas/spec.md

**Estado: borrador**

## Contexto y objetivo
El microservicio expone estadísticas agregadas de `personajes`, `atletas` y `tripulaciones`,
pero no ofrece una vista global de las recompensas de los personajes. Un chat de IA
(conectado vía n8n) necesita responder preguntas sobre recompensas (cuánto suman, cuánto
promedian, cuál es la mayor y la menor) con una respuesta clara y estable. El objetivo es
añadir un resumen global de recompensas en un único endpoint de solo lectura, reutilizable
por ese chat. El nuevo endpoint **complementa** al ya existente `/estadisticas/resumen`,
sin reemplazarlo ni modificarlo.

## Usuarios
- Chat de IA (conectado con n8n) que consulta el endpoint para responder preguntas.
- Desarrollador/consumidor de la API que inspecciona el contrato en `/docs`.

## Historias de usuario
- Como chat de IA, quiero un resumen global de recompensas, para responder cuánto suman y
  cuánto promedian las recompensas de los personajes.
- Como chat de IA, quiero conocer la recompensa máxima y mínima y cuántos personajes hay,
  para dar respuestas completas sobre el extremo superior e inferior.
- Como consumidor de la API, quiero un contrato estable y claro, para integrarlo sin
  sorpresas.

## Definiciones
- **Personaje**: documento de la colección `personajes`.
- **Recompensa**: valor numérico del campo `recompensa` de un personaje; si el campo no existe
  o es `null`, se considera `0`. Cada recompensa se convierte a entero redondeando al más
  cercano y, si la parte fraccionaria es exactamente `.5`, hacia arriba, **antes de agregar**.
  Las recompensas son berries, por lo que `total`, `promedio`, `máximo` y `mínimo` son enteros.
- **Promedio**: suma de recompensas dividida entre la cantidad de personajes, redondeada al
  entero más cercano; si la parte fraccionaria es exactamente `.5`, se redondea hacia arriba
  (p. ej. `2.5 → 3`). El cálculo se hace con **aritmética entera** (sin `float` ni `Decimal`),
  por lo que no depende del redondeo por defecto de Python ni de la coma flotante.
- **Cantidad de personajes**: número total de documentos de `personajes`.

## Requisitos funcionales (RF)
| ID | Requisito (en EARS) |
|---|--------------------|
| RF-1 | CUANDO un cliente envía `GET /estadisticas/recompensas/resumen`, EL SISTEMA responde con código `200`. |
| RF-2 | CUANDO un cliente envía `GET /estadisticas/recompensas/resumen`, EL SISTEMA devuelve un objeto JSON con los campos `cantidad_personajes`, `total_recompensas`, `promedio_recompensa`, `recompensa_maxima` y `recompensa_minima`, y ningún otro campo. Cada campo es un valor numérico; `recompensa_maxima` es solo el número, sin el nombre del personaje. |
| RF-3 | CUANDO se responde al endpoint, EL SISTEMA calcula `cantidad_personajes` como el número total de documentos de `personajes`. |
| RF-4 | CUANDO se responde al endpoint, EL SISTEMA calcula `total_recompensas` como la suma de las recompensas ya convertidas a entero de todos los personajes, contando como `0` los personajes sin campo `recompensa` o con `recompensa` `null`. |
| RF-5 | CUANDO se responde al endpoint, EL SISTEMA calcula `promedio_recompensa` como `total_recompensas` dividido entre `cantidad_personajes`, redondeado al entero más cercano con aritmética entera (sin `float` ni `Decimal`), y SI la parte fraccionaria es exactamente `.5`, ENTONCES redondea hacia arriba (p. ej. `2.5 → 3`). |
| RF-6 | CUANDO se responde al endpoint, EL SISTEMA calcula `recompensa_maxima` como la mayor recompensa entera entre todos los personajes, contando como `0` los personajes sin campo `recompensa` o con `recompensa` `null`. |
| RF-7 | CUANDO se responde al endpoint, EL SISTEMA calcula `recompensa_minima` como la menor recompensa entera entre todos los personajes, contando como `0` los personajes sin campo `recompensa` o con `recompensa` `null` (el mínimo puede ser `0`). |
| RF-8 | SI la colección de personajes está vacía, ENTONCES EL SISTEMA devuelve `200` con `cantidad_personajes`, `total_recompensas`, `promedio_recompensa`, `recompensa_maxima` y `recompensa_minima` todos iguales a `0`. |
| RF-9 | EL SISTEMA SIEMPRE incluye los cinco campos con los nombres exactos indicados, con valores numéricos enteros. |

## Requisitos no funcionales (RNF)
| ID | Requisito |
|---|-----------|
| RNF-1 | El endpoint es de solo lectura: no crea, modifica ni borra datos. |
| RNF-2 | La respuesta es determinista para el mismo estado de los datos. |
| RNF-3 | El contrato (ruta, método, código y forma del JSON) es estable para el consumidor. |
| RNF-4 | Toda la documentación, mensajes y textos de la spec están en español. |

## Casos límite
- Colección `personajes` vacía → los cinco campos en `0` (RF-8).
- Colección con personajes pero sin ninguna recompensa → `cantidad_personajes > 0` y los otros cuatro campos en `0` (RF-3, RF-4, RF-5, RF-6, RF-7).
- Personajes con `recompensa` `0` → cuentan en `cantidad_personajes`, `total` y `mínimo` (RF-3, RF-4, RF-7).
- Personajes sin campo `recompensa` o con `recompensa` `null` → se cuentan como `0` y participan en `recompensa_maxima` y `recompensa_minima` (RF-4, RF-6, RF-7).
- Recompensa no entera → se redondea (`.5` hacia arriba) antes de agregar (RF-4, RF-6, RF-7).
- Un único personaje → `promedio_recompensa`, `recompensa_maxima` y `recompensa_minima` iguales a su recompensa.
- Promedio con fracción exacta `.5` → redondeo hacia arriba (RF-5).
- Petición con método distinto de `GET` → respondida como método no permitido por el framework.

## Fuera de alcance
- Endpoint por personaje, filtros ni paginación.
- Recompensas de atletas u otras colecciones.
- Escritura de datos o recálculo/corrección de campos almacenados.
- Modificar o sustituir el endpoint existente `/estadisticas/resumen`.
- Autenticación o autorización.

## Criterios de finalización
- `GET /estadisticas/recompensas/resumen` responde `200` con los cinco campos y solo esos (RF-1, RF-2).
- Los valores de `cantidad_personajes`, `total_recompensas`, `promedio_recompensa`, `recompensa_maxima` y `recompensa_minima` coinciden con los datos (RF-3–RF-7), verificable por test y por Chrome DevTools en `/docs` y la URL del endpoint.
- Con la colección vacía, los cinco campos son `0` (RF-8).
- Con personajes pero sin ninguna recompensa, `cantidad_personajes > 0` y los otros cuatro campos son `0` (RF-3–RF-7).
- El endpoint existente `/estadisticas/resumen` no cambia.
- Los tests solo usan la base `onepiece_test` y pasan.

## Dudas abiertas
- [RESUELTO] Las recompensas se convierten a entero (`.5` hacia arriba) antes de agregar; los cinco campos son enteros.
- [RESUELTO] Un campo `recompensa` ausente o `null` vale `0` y participa en `recompensa_maxima` y `recompensa_minima` (el mínimo puede ser `0`).
- [RESUELTO] Colección con personajes pero sin recompensas: `cantidad_personajes > 0` y los otros cuatro campos en `0`.
- [RESUELTO] `recompensa: null` se trata igual que el campo ausente.
- [RESUELTO] El promedio se calcula con aritmética entera (sin `float` ni `Decimal`).
- [RESUELTO] El endpoint complementa a `/estadisticas/resumen` (no lo reemplaza); `recompensa_maxima` es solo el número, sin nombre.
- [RESUELTO] Se mantiene `cantidad_personajes` como nombre del campo.
