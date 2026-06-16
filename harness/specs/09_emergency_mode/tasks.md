# Tasks — Modo Manual de Emergencia

> Feature 9 — emergency_mode  
> Orden de implementación. Cada task debe marcarse `[x]` al completarse.

---

## Fase 1: Modelo de datos y migración

- [x] T1 — Crear modelo ORM `EmergencyModeLog` en `src/models.py` con todas las
  columnas, FK e índices definidos en `design.md` (usando
  `BigInteger().with_variant(Integer, "sqlite")` para compatibilidad con tests).
  Cubre: R15.

- [x] T2 — Crear migración SQL para producción:
  `database/migrations/2026_06_16_000001_create_emergency_mode_log.sql`
  con el CREATE TABLE completo (columnas, FK, índices).
  Cubre: R15.

---

## Fase 2: Lógica core (parser SMS y servicio)

- [x] T3 — Implementar función `parse_emergency_sms(text: str) -> ParsedSmsCommand`
  en `src/emergency_mode.py` con los patrones:
  - `"manual on"` → activate, 1440 min
  - `"manual on <N>h"` → activate, N*60 min
  - `"manual on <N>m"` → activate, N min
  - `"manual on ext <N>h"` / `"manual on ext <N>m"` → extend
  - `"manual off"` → deactivate
  - cualquier otro → invalid
  - **Case-insensitive**, tolerancia a espacios extra.
  Cubre: R6, R7, R8, R9, R16.

- [x] T4 — Implementar excepciones `EmergencyModeError`, `InvalidSmsCommandError`,
  `UnauthorizedSenderError` en `src/emergency_mode.py`.
  Cubre: (soporte estructural para todas las requirements).

- [x] T5 — Implementar clase `EmergencyModeService` en `src/emergency_mode.py`:
  - Constructor: `__init__(db_session_factory, sms_service, modem_index, dev_mode)`
  - Método `create_request(analyst_id, supervisor_id, motivo) -> int`:
    - Validar que supervisor_id exista y sea admin activo
    - Validar motivo no vacío
    - Insertar registro con status='pending', cmd_source='ui', cmd_raw='ui_request'
    - Enviar SMS al supervisor via SMSService.send_sms()
    - Retornar request_id
  - Método `is_active() -> bool`
  - Método `get_status() -> dict` con active, expires_at, remaining_seconds, active_record_id
  Cubre: R1, R2, R3, R4, R5, R11, R18.

- [x] T6 — Implementar en `EmergencyModeService`:
  - Método `activate(request_id, supervisor_id, duration_minutes, cmd_raw, cmd_source)`
    - Insertar registro con status='active'
    - Si existe solicitud previa (request_id), actualizar su status a 'cancelled' y vincular mediante `request_id`
    - Cancelar otras solicitudes `pending` al mismo supervisor (R5)
    - Si ya había un modo activo, registrar el anterior como `cancelled` primero (R12)
  - Método `extend(supervisor_id, extra_minutes, cmd_raw)`
    - Validar que modo esté activo (R19)
    - Sumar minutos a expires_at
    - Insertar registro con status='extended'
  - Método `deactivate(supervisor_id, cmd_raw)`
    - Marcar registro activo como 'cancelled' con updated_at
    - Insertar registro de cierre
  - Método `restore_from_db()`:
    - Buscar último registro con status='active' y expires_at > ahora
    - Si existe, restaurar estado
    - Si expires_at <= ahora, marcar como 'expired'
  Cubre: R5, R6, R7, R8, R9, R10, R11, R12, R14, R15, R18, R19.

- [x] T7 — Implementar en `EmergencyModeService`:
  - Método `process_incoming_sms(sender_phone, text)`:
    - Buscar usuario por número de teléfono
    - Si no existe o rol != admin → registrar como `unauthorized` (R17)
    - Parsear texto con `parse_emergency_sms()`
    - Si invalid → registrar como `invalid` (R16)
    - Delegar en activate/extend/deactivate según corresponda
  - Tarea asyncio `_check_expiry_loop()`:
    - Loop cada 30 segundos
    - Si activo y datetime.utcnow() >= expires_at, llamar a `deactivate(None, "auto_expire")`
  Cubre: R10, R16, R17.

- [x] T8 — Implementar tarea asyncio `_poll_incoming_sms()` en `EmergencyModeService`:
  - En DEV_MODE=true: usar cola interna simulada (sin mmcli)
  - En DEV_MODE=false: ejecutar `mmcli -m <idx> --messaging-list-sms` cada 15s
  - Extraer IDs, leer cada SMS con `mmcli -s <id>`
  - Extraer campo `number` y `text` de la salida
  - Llamar a `process_incoming_sms(sender, text)`
  - Eliminar SMS procesado con `mmcli -s <id> --delete`
  - Métodos `start()` / `stop()` para lanzar/cancelar las tareas
  Cubre: R6, R7, R8, R9, R11, R12, R16, R17.

---

## Fase 3: Endpoints API REST

- [x] T9 — Definir Pydantic models `EmergencyRequest` en `src/emergency_mode.py`
  con campos `supervisor_id: int` y `motivo: str` (min_length=1).
  Cubre: R1, R3.

- [x] T10 — Implementar endpoint `GET /api/emergency/admins` en
  `emergency_router`:
  - Dependencias: `check_inactivity` (cualquier rol autenticado)
  - Consulta: `User.role == "admin" AND User.is_active == True`
  - Retorna lista con id, full_name, document
  Cubre: R2.

- [x] T11 — Implementar endpoint `POST /api/emergency/request` en
  `emergency_router`:
  - Dependencias: `check_inactivity`, `get_current_user`
  - Body: `EmergencyRequest`
  - Llama a `EmergencyModeService.create_request()`
  - Retorna 200 con request_id
  - Si supervisor_id inválido o motivo vacío → 422
  Cubre: R1, R3, R4, R5.

- [x] T12 — Implementar endpoint `GET /api/emergency/status` en
  `emergency_router`:
  - Dependencias: `check_inactivity` (cualquier rol autenticado)
  - Retorna estado actual: active, expires_at, remaining_seconds
  Cubre: R13.

- [x] T13 — Registrar `emergency_router` con `app.include_router()` en
  `src/main.py`. Inicializar `EmergencyModeService` en el lifespan:
  - Instanciar con `SessionLocal`, `app.state.sms_service`, modem_index, dev_mode
  - Llamar a `restore_from_db()`
  - Llamar a `service.start()` al inicio del lifespan
  - Llamar a `service.stop()` al final del lifespan (cleanup)
  - Almacenar en `app.state.emergency_service`
  Cubre: R14.

---

## Fase 4: Integración con pesaje (campo de peso editable)

- [x] T14 — Modificar el endpoint/flujo de captura de pesaje en
  `src/weighings.py` (o `src/main.py`) para que, MIENTRAS el modo manual esté
  activo, el backend permita al operador enviar valores de peso editados
  manualmente sin requerir lectura de báscula. El frontend consulta
  `GET /api/emergency/status` para habilitar la edición.
  Cubre: R13.

---

## Fase 5: Tests

- [x] T15 — Crear `tests/test_emergency_mode.py` con `TestSmsParser`:
  - `test_parse_manual_on` → `manual on` → activate 1440 min
  - `test_parse_manual_on_4h` → `manual on 4h` → activate 240 min
  - `test_parse_manual_on_30m` → `manual on 30m` → activate 30 min
  - `test_parse_manual_on_ext_2h` → `manual on ext 2h` → extend 120 min
  - `test_parse_manual_on_ext_45m` → `manual on ext 45m` → extend 45 min
  - `test_parse_manual_off` → `manual off` → deactivate
  - `test_parse_case_insensitive` → `MANUAL ON` → activate 1440 min
  - `test_parse_invalid` → texto no reconocido → invalid
  - `test_parse_extra_spaces` → `  manual   on  ` → invalid (no match estricto)
  Cubre: R6, R7, R8, R9, R16.

- [x] T16 — Anadir `TestEmergencyModeService` en `tests/test_emergency_mode.py`:
  - Usar SQLite en memoria y `SessionLocal` real
  - `test_activate_default_duration` → activar con 'manual on' → expires_at = now + 24h
  - `test_activate_custom_duration` → activar con 'manual on 2h' → expires_at = now + 2h
  - `test_extend_active` → extender 30m sobre activo → expires_at se incrementa 30m
  - `test_extend_inactive_raises` → extender sin activo → error/log registrado
  - `test_deactivate` → desactivar → active=False, status='cancelled'
  - `test_auto_expire` → expires_at en pasado → check_expiry desactiva
  - `test_restore_from_db_active` → insertar registro active con futuro → restore → active=True
  - `test_restore_from_db_expired` → insertar registro active con pasado → restore → active=False, status='expired'
  - `test_create_request_sends_sms` → create_request → SMSService.send_sms() llamado
  - `test_create_request_invalid_supervisor` → supervisor_id no admin → ValueError
  - `test_create_request_empty_motivo` → motivo vacío → ValueError
  - `test_multiple_requests_first_wins` → 2 solicitudes a distintos admins, 1ra respuesta activa, 2da se registra como cancelled
  - `test_reactivate_while_active_renews_timer` → activo, nuevo 'manual on' → expires_at se renueva
  Cubre: R4, R5, R6, R7, R8, R9, R10, R11, R12, R14, R15, R18, R19.

- [x] T17 — Anadir `TestEmergencyModeAPI` en `tests/test_emergency_mode.py`:
  - Usar TestClient de FastAPI con BD en memoria
  - `test_get_admins` → GET /api/emergency/admins → lista de admins
  - `test_get_admins_requires_auth` → sin token → 401
  - `test_create_request` → POST /api/emergency/request con body válido → 200 + request_id
  - `test_create_request_empty_motivo` → POST con motivo="" → 422
  - `test_get_status` → GET /api/emergency/status → active, expires_at
  - `test_get_status_requires_auth` → sin token → 401
  Cubre: R1, R2, R3, R13.

- [x] T18 — Anadir `TestSmsPolling` en `tests/test_emergency_mode.py`:
  - `test_incoming_sms_activate` → simular SMS entrante 'manual on' → modo se activa
  - `test_incoming_sms_unauthorized_sender` → número no admin → se ignora, se loggea
  - `test_incoming_sms_invalid_command` → texto inválido → se ignora, se loggea
  Cubre: R6, R11, R16, R17.

---

## Fase 6: Verificación

- [x] T19 — Ejecutar todos los tests:
  `docker compose exec backend python -m unittest discover -s tests -v`
  y verificar que todos pasan (incluyendo tests existentes de features 1-7).
  Cubre: todas.

- [ ] T20 — Verificar migración en BD de producción (EdgeBox):
  - Copiar el archivo de migración a la EdgeBox
  - Ejecutar el CREATE TABLE manualmente en MariaDB
  - Verificar que la tabla `emergency_mode_log` existe con la estructura correcta
  - Verificar que la app arranca sin errores y restaura el estado desde BD
  Cubre: R14, R15.
  **PENDIENTE: Requiere acceso a la EdgeBox para verificación de hardware (Nivel 4).**
