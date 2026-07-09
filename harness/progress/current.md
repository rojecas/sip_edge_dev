# Sesion activa - 2026-07-09 - Diagnostico Bug #29 y analisis de gaps ERS vs SDD

## Resumen
Sesion dedicada a:
1. Correccion Bug #29 (scale_service_async_crashes) — CONFIRMADO y CORREGIDO
2. Descubrimiento de gaps criticos entre el ERS RF-003 y la implementacion de F13
3. Identificacion de fallo en el harness: falta de revision del spec contra el ERS

## Bug #29 — CORREGIDO

### Diagnosticos realizados
- Nivel 1 (Pipeline interno): Datos llegan desde PC por RS485, se parsean, encolan y desencolan ?
- Nivel 2 (WebSocket): Cliente recibe mensajes JSON con peso en vivo ?
- Nivel 3 (UI Kiosko): ScaleReader muestra peso en vivo ?
- Bug #2a: Cola ahora se drena en el while loop (antes solo al hacer stop)
- Bug #2b: Event loop de uvicorn almacenado en variable _event_loop (antes se creaba loop nuevo desde thread background)
- Bug #3: logging.basicConfig() movido ANTES de ScaleService.start() (antes el log 'ScaleService started' se perdia)
- Bug #1: _recover_serial() con backoff exponencial y reintentos (antes el hilo moria con break)

### Pendiente de prueba
- Nivel 6 (Recuperacion serial) — no se probo aun

## Gaps ERS vs SDD (criticos)

### RF-003 / R15 — Boton Leer
- ERS RF-003: Al presionar boton Leer, el sistema DEBE enviar comando REXT al RS485
- SDD R15 (F13): toma el valor actual del peso en vivo del WebSocket
- Real: Lee el ultimo valor del WebSocket (NO envia REXT)
- **Conclusion: R15 es incorrecto respecto al ERS**

### RF-003 / R16 — Boton Tara
- ERS RF-003: Al presionar boton Tara, el sistema DEBE enviar comando TARE al RS485
- SDD R16 (F13): DEBE enviar el comando de tara a la bascula via API
- Real: Solo pone el campo a 0 localmente, NO envia TARE
- **Conclusion: R16 correcto en spec pero no implementado**

### RF-003 — Foco + PRINT
- ERS RF-003: Escucha asincrona de datos entrantes desde la balanza (boton PRINT)
- Real: No existe auto-captura por foco
- **Conclusion: No implementado**

## Fallo del harness detectado

El flujo SDD actual es:
`
ERS ? spec-author ? [SIN REVISION] ? spec ? implementer ? reviewer ? done
`

El reviewer solo verifica implementer vs spec, NUNCA spec vs ERS.
Esto permitio que R15 contradijera RF-003 sin ser detectado.

Se necesita agregar una etapa de **spec-review** donde un revisor valide
que cada R<n> del spec se mapea correctamente a un RF del ERS, antes
de pasar a in_progress.

## Acciones pendientes
1. Corregir F13: Leer debe enviar REXT y capturar respuesta
2. Corregir F13: Tara debe enviar TARE al RS485
3. Implementar auto-captura por foco + PRINT
4. Agregar spec-review al harness
5. Cerrar Bug #29 formalmente