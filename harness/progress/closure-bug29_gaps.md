# Cierre de sesion — 2026-07-09 — Diagnostico Bug #29 y gaps ERS

## Resumen
Sesion dedicada al diagnostico y correccion de Bug #29 (scale_service_async_crashes).
Durante las pruebas se descubrieron gaps criticos entre el ERS RF-003 y la implementacion
del feature 13 (frontend_login_kiosk), y un fallo estructural en el harness.

## Logros

### Bug #29 — CORREGIDO Y CERRADO
- Bug 1: _recover_serial() con backoff exponencial (1s-8s), max 5 reintentos. 
  TypeError agregado a excepciones recuperables.
- Bug 2a: _process_async_queue() movido DENTRO del while loop.
  Los datos se desencolan y el callback se dispara en vivo.
- Bug 2b: variable _event_loop guardada durante lifespan (uvicorn loop).
  _on_scale_data usa este loop en vez de _resolve_event_loop() desde thread background.
- Bug 3: logging.basicConfig() movido ANTES de ScaleService.start().
- Prueba: datos reales desde PC (COM1 -> RS485) hasta WebSocket del kiosko (Niveles 0-3)

### Hallazgos — Gaps ERS vs Implementation
- ERS RF-003 dice: Leer debe enviar REXT; Tara debe enviar TARE
- R15 del spec dice: Leer toma valor del WebSocket (incorrecto vs ERS)
- R16 del spec dice bien pero no se implemento
- Foco + PRINT no existe

### Hallazgo — Fallo del harness
- El flujo SDD no tiene revision del spec contra el ERS
- spec-author traduce ERS -> spec sin supervisión
- reviewer solo verifica implementer vs spec
- Se necesita agregar etapa de spec-review

## Estado del repositorio
- Commit: 8d91c8e
- Bug #29: done
- F13 (frontend_login_kiosk): blocked (spec necesita revision vs ERS)
- EdgeBox: deployado con fix de Bug #29 + fix de WeightField.svelte (prefijo $ faltante)

## Pendiente para proxima sesion
1. Reabrir F13 — contrastar spec/13_frontend_login_kiosk/ contra ERS RF-003
2. Identificar Rs faltantes y Rs mal definidos
3. Corregir spec, implementar Leer->REXT, Tara->TARE, foco+PRINT
4. Agregar spec-review al harness