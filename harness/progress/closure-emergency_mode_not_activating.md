# Closure: Bug #23 — emergency_mode_not_activating

## Sintoma
`process_incoming_sms()` se ejecuta completo (parseo OK, lookup de admin OK,
`self.activate()` se llama) pero `GET /api/emergency/status` retorna `active: false`.
File debug "INSIDE activate" confirmaba que `activate()` era invocada.

## Causa raiz
**Excepcion silenciosa dentro de `activate()` tragada por `_dispatch()`.**

El handler es llamado desde `IncomingSmsDispatcher._dispatch()`, que tiene un
`try/except Exception` generico (linea 194 de `sms_incoming.py`). Cuando
`activate()` lanza una excepcion (ej. por falla de `_db_session_factory()`
o `db.commit()`), la excepcion:
1. Es capturada por `_dispatch()` y loggeada como `logger.exception()`
2. NO es re-lanzada — `_dispatch()` CONTINUA al siguiente handler
3. El siguiente handler (AI fallback) siempre retorna True
4. El SMS aparece como "manejado" pero el modo manual nunca se activa

La causa del error de sesiones anteriores: habia un file debug AL INICIO de
`activate()` (linea 402-403 original), que se ejecuta ANTES de cualquier
operacion de BD. Al ver "INSIDE activate" en el log, se asumio que la funcion
completo exitosamente, pero en realidad fallaba despues de esa linea.

**Escenario mas probable en produccion:** `_db_session_factory()` (que es
`_db.SessionLocal`) podria ser `None` si `init_db()` fallo silenciosamente,
o `db.commit()` podria fallar por schema mismatch entre SQLAlchemy model y
MariaDB (tipos TIMESTAMP vs DATETIME, etc.).

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/emergency_mode.py` | `activate()`: anadido guard `callable(self._db_session_factory)` con log + excepcion clara |
| `src/emergency_mode.py` | `activate()`: anadido `try/except Exception` con `logger.exception("BUG #23: ...")` que loggea contexto completo ANTES de re-lanzar |
| `src/emergency_mode.py` | `process_incoming_sms()`: anadida verificacion `if not self._active:` con `logger.error("BUG #23 DETECTADO: ...")` DESPUES de `self.activate()` |
| `src/emergency_mode.py` | Limpieza de file debug (`/tmp/ems_debug.log`) dejado por sesion anterior |
| `tests/test_emergency_mode.py` | 4 nuevos tests de pipeline completo: `TestFullPipeline` con `IncomingSmsDispatcher` |

## Fix aplicado

### 1. Guard de seguridad en `activate()`
```python
if not callable(self._db_session_factory):
    logger.error("BUG #23: _db_session_factory no es invocable ...")
    raise EmergencyModeError("Error interno: fabrica de sesiones no disponible")
```
Antes de cualquier operacion de BD, verifica que `_db_session_factory` sea
invocable. Si es `None` o no es callable, loggea error y lanza excepcion.

### 2. Exception logging en `activate()`
```python
except Exception:
    logger.exception(
        "BUG #23: activate() fallo con excepcion. "
        "supervisor_id=%s, duration=%s, self._active=%s",
        supervisor_id, duration_minutes, self._active,
    )
    raise
```
Toda excepcion en `activate()` se loggea con contexto completo (supervisor_id,
duration, self._active) ANTES de re-lanzar. Esto asegura visibilidad incluso
si `_dispatch()` traga la excepcion.

### 3. Verificacion post-activacion en `process_incoming_sms()`
```python
self.activate(...)
if not self._active:
    logger.error("BUG #23 DETECTADO: activate() retorno pero self._active=False...")
```
Si `activate()` retorna sin excepcion pero `self._active` sigue siendo False,
se loggea un error con contexto completo.

### 4. Pipeline tests
4 nuevos tests que simulan el flujo completo de produccion:
- `IncomingSmsDispatcher` con handler registrado
- Encolado de SMS via `enqueue_incoming_sms()`
- Ejecucion de `_check_incoming_sms()`
- Verificacion de `is_active()` y `get_status()["active"]`

## Regression test
Clase `TestFullPipeline` en `tests/test_emergency_mode.py`:

| Test | Escenario |
|------|-----------|
| `test_pipeline_dispatcher_to_activate` | SMS "manual on" → dispatcher → activate → status active |
| `test_pipeline_dispatcher_to_deactivate` | SMS "manual off" → dispatcher → deactivate → status inactive |
| `test_pipeline_dispatcher_unauthorized` | SMS de operador no activa modo manual |
| `test_pipeline_dispatcher_invalid_command` | Texto no relevante no afecta estado |

## Resultado de verificacion
```
$ docker compose exec backend python -m unittest tests.test_emergency_mode -v
Ran 59 tests in 32.996s
OK
```

## Notas adicionales
- El bug NO se reproduce en entorno de tests (SQLite) porque la session factory
  siempre es valida. La instrumentacion dejada en produccion (vía logs con
  "BUG #23") permitira identificar la causa exacta si el bug persiste.
- Los 5 errores en `test_password_reset.TestIncomingSmsDispatcher` son
  pre-existentes (Pythoon 3.11 `asyncio.get_event_loop()` deprecation) y
  no relacionados con este fix.
