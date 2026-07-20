# Feature 39 — Trazabilidad: Registro de usuario creador en Haciendas y Suertes

## R1
CUANDO se ejecuta la migración `2026_07_19_000001_add_created_by_to_haciendas`,
el sistema DEBE agregar la columna `created_by` tipo `BIGINT UNSIGNED NULL`
a la tabla `haciendas` con FK a `users(id)`.

## R2
CUANDO se ejecuta la migración `2026_07_19_000002_add_created_by_to_suertes`,
el sistema DEBE agregar la columna `created_by` tipo `BIGINT UNSIGNED NULL`
a la tabla `suertes` con FK a `users(id)`.

## R3
CUANDO un usuario autenticado envía `POST /api/haciendas` con un body válido,
el sistema DEBE asignar el valor de `created_by` igual al `user_id` del token JWT
del usuario autenticado.

## R4
CUANDO un usuario autenticado envía `POST /api/suertes` con un body válido,
el sistema DEBE asignar el valor de `created_by` igual al `user_id` del token JWT
del usuario autenticado.

## R5
CUANDO el sistema responde a `GET /api/haciendas` o `GET /api/haciendas/{id}`,
la respuesta DEBE incluir los campos `created_by` (int | None) y
`created_by_username` (str | None) en cada item del array `items`.

## R6
CUANDO el sistema responde a `GET /api/suertes` o `GET /api/suertes/{id}`,
la respuesta DEBE incluir los campos `created_by` (int | None) y
`created_by_username` (str | None) en cada item.

## R7
CUANDO el componente `AdminHaciendas.svelte` renderiza la tabla de haciendas
(en las vistas admin y kiosko), DEBE mostrar una columna adicional "Creado por"
cuyo valor es el `created_by_username` del registro, o "—" si es NULL.

## R8
CUANDO el componente `AdminSuertes.svelte` renderiza la tabla de suertes
(en las vistas admin y kiosko), DEBE mostrar una columna adicional "Creado por"
cuyo valor es el `created_by_username` del registro, o "—" si es NULL.

## R9
MIENTRAS existan registros en `haciendas` o `suertes` creados antes de esta
migración, el sistema DEBE exponer `created_by = null` y
`created_by_username = null` para esos registros, sin errores ni
conversiones forzadas.

## R10
CUANDO se crea una hacienda o suerte sin token de autenticación (HTTP 401),
el sistema DEBE rechazar la operación antes de intentar asignar `created_by`,
devolviendo el mismo error que el comportamiento actual.
