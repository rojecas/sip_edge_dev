# Requirements — Integracion Serial con Bascula DINI ARGEO DFWLI-2

> Feature: RF-003. EARS notation.

---

## R1
CUANDO el sistema inicia, la aplicacion DEBE instanciar `ScaleService` como
singleton en `app.state` con la configuracion del puerto RS485 (`path`,
`baudrate`, `timeout_seconds`) cargada desde `config.yaml`.

## R2
CUANDO `ScaleService.send_command("REXT")` es invocado, el sistema DEBE
enviar `00REXT\r\n` al puerto RS485, esperar la respuesta extendida, y
devolver un dict con `status`, `weight`, `tare`, `unit`, `is_stable`.

## R3
CUANDO `ScaleService.send_command("TARE")` es invocado, el sistema DEBE
enviar `00TARE\r\n` al puerto RS485 y devolver un dict con `{"result":
"ok"}` si la balanza responde `OK\r\n`.

## R4
CUANDO `ScaleService.send_command("TMAN", value="1.56")` es invocado,
el sistema DEBE enviar `00TMAN1.56\r\n` al puerto RS485 y devolver un
dict con `{"result": "ok"}` si la balanza responde `OK\r\n`.

## R5
CUANDO `ScaleService.send_command("ZERO")` es invocado, el sistema DEBE
enviar `00ZERO\r\n` al puerto RS485 y devolver un dict con `{"result":
"ok"}` si la balanza responde `OK\r\n`.

## R6
CUANDO `ScaleService.send_command("CLEAR")` es invocado, el sistema DEBE
enviar `00CLEAR\r\n` al puerto RS485 y devolver un dict con `{"result":
"ok"}` si la balanza responde `OK\r\n`.

## R7
CUANDO `ScaleService.send_command` recibe una respuesta extendida como
`01ST,1, 0.0,PT 20.8, 0,kg\r\n`, el sistema DEBE parsear los campos en
un dict: `{"address": "01", "status_code": "ST", "is_stable": true,
"net_weight": 0.0, "tare_indicator": "PT", "tare_weight": 20.8,
"piece_count": 0, "unit": "kg"}`.

## R8
CUANDO `ScaleService.send_command` recibe una respuesta corta como
`01US,GS, 5.2,kg\r\n`, el sistema DEBE parsear los campos en un dict:
`{"address": "01", "status_code": "US", "is_stable": false, "weight":
5.2, "unit": "kg"}`. NO DEBE devolver campos de tara ni piezas.

## R9
SI `ScaleService.send_command` no recibe respuesta dentro del timeout
configurado (`scale.timeout_seconds`), el sistema DEBE lanzar una
excepcion `ScaleTimeoutError`.

## R10
SI `ScaleService.send_command` recibe una respuesta inesperada (no
reconocible como respuesta extendida, corta u `OK`), ENTONCES el
sistema DEBE lanzar una excepcion `ScaleProtocolError`.

## R11
MIENTRAS `ScaleService` esta activo, el sistema DEBE ejecutar un hilo
en background que lea datos entrantes del puerto RS485 de forma
asincrona y los ponga en una cola interna (`queue.Queue`).

## R12
CUANDO el hilo asincrono recibe una respuesta extendida o corta, el
sistema DEBE invocar la funcion `callback` proporcionada en
`async_listener(callback)` con el dict parseado como argumento.

## R13
CUANDO un admin autenticado hace `PUT /api/setup/scale` con
`timeout_seconds: N`, el sistema DEBE guardar `N` en `config.yaml`
bajo la seccion `scale.timeout_seconds` y actualizar la configuracion
en memoria del `ScaleService`. El rango valido es 1–10.

## R14
SI `timeout_seconds` en `PUT /api/setup/scale` esta fuera del rango
1–10, ENTONCES el sistema DEBE devolver HTTP 422.

## R15
SI un usuario NO autenticado accede a `PUT /api/setup/scale` ENTONCES
el sistema DEBE devolver HTTP 401.

## R16
SI un usuario autenticado con rol distinto de "admin" accede a
`PUT /api/setup/scale` ENTONCES el sistema DEBE devolver HTTP 403.
