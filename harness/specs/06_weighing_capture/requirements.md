# Requirements — Captura de Pesaje Multipaso con Confirmacion y Envio RS232

> Feature: RF-004, RF-005. EARS notation.

---

## R1
CUANDO un operador autenticado hace `GET /api/haciendas`, el sistema DEBE
devolver la lista de haciendas activas (mismo comportamiento que
feature 4, pero accessible por rol operator).

## R2
CUANDO un operador autenticado hace `GET /api/suertes?hacienda_id=X`,
el sistema DEBE devolver las suertes activas de esa hacienda
(mismo comportamiento que feature 4, pero accessible por rol operator).

## R3
CUANDO un operador autenticado hace `POST /api/weighings` con un body
que incluye `tractomula`, `vagon`, `numero_guia`, `hacienda_id`,
`suerte_id`, `peso_muestra`, `peso_mineral`, `peso_vegetal_extrano`,
el sistema DEBE crear un registro en la tabla `weighings` y devolverlo
con HTTP 201.

## R4
CUANDO `POST /api/weighings` crea un registro exitosamente, el sistema
DEBE invocar `send_frame(frame_data, format="json")` desde el modulo
`src.rs232` para transmitir la trama al PC externo vía RS232.

## R5
CUANDO `POST /api/weighings` persiste el registro y envía la trama
RS232, el sistema DEBE devolver el registro creado con todos sus
campos, incluyendo `id`, `fecha`, `hora` y el resto de columnas de
la tabla `weighings`.

## R6
SI `POST /api/weighings` falla al persistir en MariaDB, ENTONCES el
sistema DEBE hacer rollback de la transacción y NO DEBE invocar
`send_frame`. El sistema DEBE devolver HTTP 500.

## R7
SI `POST /api/weighings` persiste exitosamente pero `send_frame`
lanza una excepción (el envío RS232 falla), ENTONCES el sistema DEBE
registrar el error en el log pero NO DEBE hacer rollback de la
transacción. El campo `enviado_pc` DEBE permanecer como `FALSE`.

## R8
SI un usuario NO autenticado accede a `POST /api/weighings` ENTONCES
el sistema DEBE devolver HTTP 401.

## R9
SI un usuario autenticado con rol "admin" accede a `POST /api/weighings`
ENTONCES el sistema DEBE permitir la creación (admin también puede
pesar).

## R10
CUANDO un operador autenticado hace `GET /api/weighings`, el sistema
DEBE devolver SOLO los registros donde `usuario_id` coincide con el
usuario autenticado.

## R11
CUANDO un admin autenticado hace `GET /api/weighings`, el sistema DEBE
devolver TODOS los registros de la tabla `weighings`.

## R12
CUANDO un operador autenticado hace `GET /api/weighings/{id}`, el
sistema DEBE devolver el registro si existe y pertenece al usuario
autenticado.

## R13
CUANDO un admin autenticado hace `GET /api/weighings/{id}`, el
sistema DEBE devolver el registro si existe (sin importar el usuario).

## R14
SI el `id` en `GET /api/weighings/{id}` no existe ENTONCES el sistema
DEBE devolver HTTP 404.

## R15
SI un operador autenticado hace `GET /api/weighings/{id}` con un
registro que pertenece a otro usuario ENTONCES el sistema DEBE
devolver HTTP 404.

## R16
CUANDO un usuario autenticado hace `POST /api/weighings/reset`, el
sistema DEBE limpiar el estado temporal del formulario en backend
(si existe) y devolver HTTP 200 con un mensaje de confirmación.

## R17
MIENTRAS `ScaleService` tiene un listener asíncrono registrado, el
sistema DEBE exponer un WebSocket en `/ws/scale` que transmita a
todos los clientes conectados las lecturas espontáneas de la balanza
en tiempo real.

## R18
CUANDO un operador autenticado se conecta a `WS /ws/scale`, el sistema
DEBE enviar las lecturas de peso entrantes como mensajes JSON con
formato: `{"type": "scale_reading", "data": {"net_weight": 0.0,
"is_stable": true, "unit": "kg"}}`.

## R19
SI un usuario NO autenticado intenta conectar a `WS /ws/scale`,
ENTONCES el sistema DEBE cerrar la conexión con código 4001.

## R20
CUANDO un operador autenticado hace `POST /api/weighings` con valores
de peso no numéricos o negativos, el sistema DEBE devolver HTTP 422.

## R21
CUANDO un operador autenticado hace `POST /api/weighings`, el sistema
DEBE establecer `fecha` y `hora` automáticamente a la fecha y hora
actual del servidor. NO DEBE aceptar `fecha` ni `hora` del body.

## R22
CUANDO un operador autenticado hace `POST /api/weighings`, el sistema
DEBE establecer `usuario_id` automáticamente a partir del token JWT.
NO DEBE aceptar `usuario_id` del body.

## R23
CUANDO `POST /api/weighings` persiste exitosamente, el sistema DEBE
establecer `enviado_pc` como `TRUE` solo si `send_frame` se ejecuta
sin errores. Si `send_frame` no existe (módulo rs232 no implementado),
el sistema DEBE continuar sin error y dejar `enviado_pc = FALSE`.
