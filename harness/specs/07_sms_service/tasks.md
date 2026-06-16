# Tasks — Servicio de Notificaciones y Reportes SMS

> Feature 7 — sms_service  
> Orden de implementación. Cada task debe marcarse `[x]` al completarse.

---

- [x] T1 — Añadir columna `failed_login_attempts` al modelo `User` en
  `src/models.py`. Cubre: R3.

- [x] T2 — Añadir dataclass `SmsConfig` en `src/config.py`. Extender
  `load_config()` para parsear la sección `sms` (con defaults si no existe).
  Añadir función `save_sms_config()`. Actualizar `_atomic_write_sections()`
  para incluir la sección `sms`. Cubre: R6, R7.

- [x] T3 — Crear `src/sms_service.py` con:
  - Excepción `SMSDeliveryError`
  - Clase `SMSService` con constructor que recibe `SmsConfig`, `modem_index`,
    `dev_mode`
  - Método `send_sms(phone, message) -> bool` con lógica dual
    (mmcli / simulación)
  - Método `send_alert_to_admins(message)`
  - Método `send_scheduled_report(report_text)`
  - Método `generate_turn_report(db, turn_start, turn_end) -> str`
  - Método `start_scheduler()` / `stop_scheduler()` basado en asyncio
  Cubre: R1, R8, R9, R11.

- [x] T4 — Modificar `POST /api/auth/login` en `src/main.py`:
  - Leer y escribir `user.failed_login_attempts` en la BD
  - Incrementar contador en cada login fallido
  - Si `failed_login_attempts >= 3`, llamar a
    `app.state.sms_service.send_alert_to_admins()` y resetear contador
  - Resetear contador a 0 en login exitoso
  Cubre: R2, R3, R4.

- [x] T5 — Modificar el lifespan en `src/main.py`:
  - Desempaquetar `SmsConfig` del tuple de `load_config()`
  - Almacenar `app.state.sms_config`
  - Crear instancia de `SMSService` y almacenar en `app.state.sms_service`
  - Llamar a `sms_service.start_scheduler()`
  - En el cleanup del lifespan, llamar a `sms_service.stop_scheduler()`
  Cubre: R1, R5, R6, R7, R10.

- [x] T6 — Crear `tests/test_sms_service.py` con:
  - `TestSMSServiceDevMode` — verificar que en DEV_MODE=true se simula sin
    mmcli (R9), que `send_sms` retorna True incluso en simulación (R1)
  - `TestSMSServiceProdMode` — verificar que en DEV_MODE=false se ejecuta
    mmcli con los argumentos correctos (mockear subprocess.run) (R1)
  - `TestSMSServiceErrorHandling` — verificar que si mmcli falla se loggea
    error y no se lanza excepción fuera de SMSService (R8)
  - `TestSMSServiceEmptyPhones` — verificar que con admin_phones vacío no se
    intenta enviar (R7)
  Cubre: R1, R7, R8, R9.

- [x] T7 — Añadir tests en `tests/test_auth.py`:
  - `test_login_failed_increments_counter` — verificar que 1 login fallido
    incrementa el contador a 1
  - `test_login_failed_triggers_alert_at_3` — verificar que en el 3er fallo
    se llama a send_alert_to_admins (mockear SMSService en app.state)
  - `test_login_failed_resets_after_alert` — verificar que tras la alerta el
    contador vuelve a 0
  - `test_login_success_resets_counter` — verificar que un login exitoso pone
    el contador a 0
  - `test_login_failed_does_not_alert_before_3` — verificar que con 1 o 2
    fallos NO se envía alerta
  Cubre: R2, R3, R4.

- [x] T8 — Crear migración SQL para producción:
  `database/migrations/2026_06_15_000001_add_failed_login_attempts_to_users.sql`
  con `ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0;`
  Cubre: R3.
