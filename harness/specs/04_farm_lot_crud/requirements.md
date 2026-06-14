# Requirements — Gestión de Haciendas y Suertes

> Feature: RF-006, RF-007, RF-008. EARS notation.

---

## R1
CUANDO un admin autenticado hace `GET /api/haciendas`, el sistema DEBE
devolver la lista de haciendas con `deleted_at IS NULL`.

## R2
CUANDO un admin autenticado hace `POST /api/haciendas` con `codigo` y `nombre`,
el sistema DEBE crear una nueva hacienda y devolverla con HTTP 201.

## R3
CUANDO un admin autenticado hace `GET /api/haciendas/{id}`, el sistema DEBE
devolver la hacienda si existe y su `deleted_at IS NULL`.

## R4
SI el `id` en `GET /api/haciendas/{id}` no existe o está eliminado (deleted_at NOT NULL)
ENTONCES el sistema DEBE devolver HTTP 404.

## R5
CUANDO un admin autenticado hace `PUT /api/haciendas/{id}` con campos a actualizar,
el sistema DEBE actualizar la hacienda y devolverla.

## R6
SI el `id` en `PUT /api/haciendas/{id}` no existe o está eliminado ENTONCES
el sistema DEBE devolver HTTP 404.

## R7
CUANDO un admin autenticado hace `DELETE /api/haciendas/{id}`, el sistema DEBE
establecer `deleted_at` a la fecha/hora UTC actual (soft delete) y devolver la
hacienda actualizada.

## R8
SI el `id` en `DELETE /api/haciendas/{id}` no existe o ya está eliminado
ENTONCES el sistema DEBE devolver HTTP 404.

## R9
CUANDO un admin autenticado hace `POST /api/haciendas` con un `codigo` ya existente
en otra hacienda activa, el sistema DEBE devolver HTTP 409.

## R10
CUANDO un admin autenticado hace `GET /api/suertes`, el sistema DEBE devolver
la lista de suertes con `deleted_at IS NULL`.

## R11
DONDE se proporciona `?hacienda_id=X` en `GET /api/suertes`, el sistema DEBE
filtrar solo las suertes no eliminadas de esa hacienda.

## R12
CUANDO un admin autenticado hace `POST /api/suertes` con `hacienda_id` y
`codigo_suerte`, el sistema DEBE crear una nueva suerte vinculada a la hacienda
y devolverla con HTTP 201.

## R13
SI el `hacienda_id` en `POST /api/suertes` no existe o está eliminado ENTONCES
el sistema DEBE devolver HTTP 404.

## R14
CUANDO un admin autenticado hace `GET /api/suertes/{id}`, el sistema DEBE
devolver la suerte si existe y su `deleted_at IS NULL`.

## R15
SI el `id` en `GET /api/suertes/{id}` no existe o está eliminado ENTONCES
el sistema DEBE devolver HTTP 404.

## R16
CUANDO un admin autenticado hace `PUT /api/suertes/{id}` con campos a actualizar,
el sistema DEBE actualizar la suerte y devolverla.

## R17
SI el `id` en `PUT /api/suertes/{id}` no existe o está eliminado ENTONCES
el sistema DEBE devolver HTTP 404.

## R18
CUANDO un admin autenticado hace `DELETE /api/suertes/{id}`, el sistema DEBE
establecer `deleted_at` a la fecha/hora UTC actual (soft delete) y devolver la
suerte actualizada.

## R19
SI el `id` en `DELETE /api/suertes/{id}` no existe o ya está eliminado ENTONCES
el sistema DEBE devolver HTTP 404.

## R20
CUANDO un admin autenticado crea una suerte con `(hacienda_id, codigo_suerte)` que
ya existe en otra suerte activa de la misma hacienda, el sistema DEBE devolver
HTTP 409.

## R21
SI un usuario NO autenticado accede a cualquier endpoint de `/api/haciendas/*`
o `/api/suertes/*` ENTONCES el sistema DEBE devolver HTTP 401.

## R22
SI un usuario autenticado con rol distinto de "admin" accede a cualquier endpoint
de `/api/haciendas/*` o `/api/suertes/*` ENTONCES el sistema DEBE devolver HTTP 403.

## R23
CUANDO un admin autenticado hace `GET /api/haciendas`, el sistema DEBE devolver
cada hacienda con sus campos: `id`, `codigo`, `nombre`, `created_at`, `updated_at`.
NO DEBE incluir `deleted_at`.

## R24
CUANDO un admin autenticado hace `GET /api/suertes` (con o sin `hacienda_id`),
el sistema DEBE devolver cada suerte con sus campos: `id`, `hacienda_id`,
`codigo_suerte`, `created_at`, `updated_at`. NO DEBE incluir `deleted_at`.
