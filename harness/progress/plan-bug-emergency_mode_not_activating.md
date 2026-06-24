# Plan de diagnostico: Bug #23 — emergency_mode_not_activating

## Sintoma
`process_incoming_sms()` se ejecuta completo (parseo OK, lookup de admin OK,
`self.activate()` se llama) pero `GET /api/emergency/status` retorna `active: false`.
El debug "INSIDE activate" prueba que `activate()` es invocada.

## Estado actual
- **55 tests unitarios pasan**, incluyendo `test_incoming_sms_activate` que prueba
  exactamente el escenario: `process_incoming_sms()` → activación → `is_active() == True`.
- El bug se manifiesta SOLO en producción (o en el pipeline completo con dispatcher).
- Hay un debug file existente (`/tmp/ems_debug.log`) con la línea "INSIDE activate"
  al inicio de `activate()` (lineas 402-403).

## Hipotesis (ordenadas por probabilidad)

### H1: Excepcion silenciosa dentro de activate() capturada por _dispatch()
El handler `process_incoming_sms` es llamado desde `_dispatch()`, que tiene un
`try/except Exception` que captura y LOGEA cualquier excepcion. Si `activate()`
lanza una excepcion, `_dispatch()` la traga y el SMS se considera "manejado".

**Puntos de falla posibles en `activate()`:**
1. `self._db_session_factory()` retorna None o session invalida
2. `db.query(User).filter(User.id == supervisor_id, ...)` no encuentra el usuario
3. `db.commit()` lanza por constraint violation o schema mismatch
4. `db.refresh()` lanza por schema issue

**Que revisar:**
- [ ] Los logs del contenedor en produccion muestran "Handler ... fallo procesando SMS"?
- [ ] Si la excepcion ocurre despues de `self._active = True` (linea 470), el estado
      quedaria como True. Si ocurre antes, quedaria como False (coincide con el bug).

### H2: Dos instancias de EmergencyModeService (singleton roto)
Si por alguna razon hay DOS instancias de `EmergencyModeService`, la instancia
que recibe el SMS via `process_incoming_sms` activaria su `_active = True`, pero
el endpoint `GET /status` leeria de OTRA instancia diferente.

**Donde verificar:**
- [ ] `request.app.state.emergency_service` en endpoint GET /status
- [ ] `app.state.emergency_service.process_incoming_sms` registrado en dispatcher
- [ ] Ambas referencias apuntan al MISMO objeto (mismo id())

### H3: La expiracion automatica se dispara inmediatamente
Si `_expires_at` se calcula incorrectamente (ej. en pasado), el expiry checker
podria desactivar inmediatamente.

**Donde verificar:**
- [ ] Valor de `expires_at` calculado en `activate()` — deberia ser futuro
- [ ] El expiry checker no corre concurrentemente a `activate()`

### H4: Schema mismatch entre MariaDB y SQLAlchemy model
La tabla `emergency_mode_log` en MariaDB podria tener un schema diferente al
modelo SQLAlchemy, causando que `db.commit()` falle con un error de constraint.

**Donde verificar:**
- [ ] La migracion `2026_06_16_000001_create_emergency_mode_log.sql` fue ejecutada
- [ ] Todas las columnas existen en MariaDB con tipos compatibles

## Plan de instrumentacion

### Fase 1: Agregar file debug granular en activate()
Anadir logs a CADA paso dentro de `activate()` para identificar exactamente
donde falla:

```
[1] Session factory llamada
[2] Supervisor query hecha → encontrado=True/False
[3] Calculo expires_at: <valor>
[4] Prev record cancelado: OK/Skip
[5] Pending requests cancelados: N registros
[6] Activation EmergencyModeLog creado
[7] db.commit() ejecutado → OK/ERROR
[8] db.refresh() ejecutado → OK/ERROR, id=<valor>
[9] self._active = True seteado
[10] SALIENDO de activate()
```

### Fase 2: Verificar identidad del singleton
Agregar log del `id(self)` en `process_incoming_sms`, `activate()`, y `get_status()`
para confirmar que es la misma instancia.

### Fase 3: Regression test
Crear test que simule el pipeline completo:
- `IncomingSmsDispatcher` con handler registrado
- Encolar SMS via `enqueue_incoming_sms()`
- Ejecutar `_check_incoming_sms()` una vez
- Verificar `svc.is_active()` y `svc.get_status()["active"]`

## Resultados esperados
Despues de la instrumentacion, ejecutar los tests y/o desplegar para ver
los logs y determinar exactamente donde falla `activate()`.

## Plan de verificacion
1. Agregar instrumentacion
2. Ejecutar tests para confirmar que siguen pasando
3. Si el bug se reproduce en tests: identificar la falla
4. Si el bug no se reproduce en tests: desplegar a EdgeBox y monitorear logs
5. Una vez identificada la causa raiz: implementar fix minimalista
