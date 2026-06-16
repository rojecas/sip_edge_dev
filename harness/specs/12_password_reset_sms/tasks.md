# Tasks — Password Reset via SMS

> Checklist ejecutable en orden. Cada paso referencia los `R<n>` que cubre.

---

## Fase 1 — Persistencia y modelo

- [x] T1 — Crear migración `database/migrations/2026_06_16_000003_add_password_reset_fields.sql`
      agregando columnas `force_password_change`, `reset_pin`, `reset_pin_expires_at` a `users`.
      Cubre: R13.

- [x] T2 — Agregar columnas `force_password_change` (Boolean, default False),
      `reset_pin` (String(128), nullable), `reset_pin_expires_at` (TIMESTAMP, nullable)
      al modelo `User` en `src/models.py`.
      Cubre: R13.

- [x] T3 — Excluir `reset_pin` y `reset_pin_expires_at` de `UserResponse` en `src/users.py`
      (campos no declarados se excluyen automáticamente con `from_attributes = True`).
      Agregar `force_password_change` a `UserResponse`.
      Cubre: R14.

---

## Fase 2 — Dispatcher compartido de SMS entrantes

- [x] T4 — Crear `src/sms_incoming.py` con la clase `IncomingSmsDispatcher` que:
      - Polling mmcli unificado cada 15 s.
      - Cola de handlers registrados `(sender_phone, text) -> bool`.
      - Soporte para dev mode con cola interna (`enqueue_incoming_sms`).
      - Métodos `start()` / `stop()` para el ciclo de vida.
      Cubre: R1, R15 (infraestructura base).

- [x] T5 — Refactorizar `EmergencyModeService` en `src/emergency_mode.py`:
      - Eliminar `_poll_incoming_sms()` y `_poll_mmcli_sms()`.
      - Eliminar `_dev_incoming_queue` y `enqueue_incoming_sms()`.
      - `process_incoming_sms` ahora retorna `bool` y actúa como handler del dispatcher.
      - Eliminar imports no usados (`subprocess`, `os`, `_SMS_ID_RE`).
      Cubre: (soporte, ningún R directo — no romper feature #9).

---

## Fase 3 — PasswordResetService

- [x] T6 — Crear `src/password_reset.py` con:
      - Clase `PasswordResetError`, `InvalidPinError`.
      - Parser `_parse_reset_command(text: str) -> str | None` que extrae username
        del patrón "reset password <username>" (case-insensitive).
      - Clase `PasswordResetService` con:
        * `handle_incoming_sms(sender_phone, text) -> bool`
        * `generate_and_send_pin(username, sender_phone) -> bool`
        * `verify_pin(username, pin) -> str`
        * `complete_reset(reset_token, new_password, confirm_password) -> None`
      - Schemas Pydantic: `VerifyResetPinRequest`, `VerifyResetPinResponse`, `CompleteResetRequest`.
      - Registro del handler en el dispatcher via `main.py`.
      Cubre: R1, R2, R3, R4, R5, R6.

- [x] T7 — Implementar en `PasswordResetService`:
      - Generación de PIN aleatorio de 4 dígitos (1000-9999).
      - Hash bcrypt del PIN con `auth.hash_password`.
      - Persistencia: `reset_pin = hash`, `reset_pin_expires_at = now + 1h`,
        `force_password_change = True`.
      - Envío de SMS al teléfono del usuario con `SMSService.send_sms()`.
      - SMS de error al remitente si usuario no existe o sin teléfono.
      Cubre: R4, R5, R6.

---

## Fase 4 — Endpoints API

- [x] T8 — Agregar en `src/auth.py` la función `create_reset_token(user_id: int) -> str`
      que genera un JWT con expiración de 5 minutos y purpose="password_reset".
      Agregar también `decode_reset_token(token: str) -> dict` para validación.
      Cubre: R8, R10.

- [x] T9 — Agregar endpoint `POST /api/auth/verify-reset-pin` en `src/password_reset.py`:
      - Schema `VerifyResetPinRequest` (username, pin).
      - Schema `VerifyResetPinResponse` (reset_token, token_type).
      - Lógica de verificación según R7, R8, R9.
      - Mensaje genérico "Invalid username or PIN" en errores (401).
      Cubre: R7, R8, R9.

- [x] T10 — Agregar endpoint `POST /api/auth/complete-reset` en `src/password_reset.py`:
      - Schema `CompleteResetRequest` (reset_token, new_password, confirm_password).
      - Lógica de cambio según R10, R11, R12.
      - HTTP 401 si token inválido/expirado, HTTP 422 si passwords no coinciden.
      Cubre: R10, R11, R12.

- [x] T11 — Registrar el router de password_reset en `src/main.py` e inicializar
      `IncomingSmsDispatcher` y `PasswordResetService` en el lifespan.
      - Registrar handlers: emergency primero, password_reset segundo.
      - Iniciar dispatcher en lifespan.
      Cubre: R15 (infraestructura).

---

## Fase 5 — Frontend

- [x] T12 — Agregar enlace "Olvidó su contraseña" en la página de login (HTML/HTMX).
      - Se creó `src/login_page.py` con página HTML completa.
      - La página se sirve en `GET /login`.
      - El modal muestra campos username + PIN (4 dígitos).
      Cubre: R15.

- [x] T13 — Implementar modal de cambio de contraseña (HTML/HTMX) que aparece tras
      verificación exitosa de PIN. Campos: nueva contraseña + confirmación.
      Llama a `POST /api/auth/complete-reset` con el `reset_token` de la respuesta.
      Cubre: R16.

---

## Fase 6 — Tests

- [x] T14 — Tests unitarios para `PasswordResetService.generate_and_send_pin()`:
      - `test_generate_pin_range` — PIN en rango 1000-9999.
      - `test_generate_pin_hash_stored` — PIN almacenado como hash.
      - `test_generate_pin_expires_at` — expires_at ≈ now + 1h.
      - `test_generate_pin_force_password_change` — flag activado.
      - `test_generate_pin_no_user` — error si usuario no existe.
      - `test_generate_pin_no_phone` — error si usuario sin teléfono.
      - `test_generate_pin_case_insensitive_username` — búsqueda case-insensitive.
      - `test_generate_pin_multiple_generations_invalidate_previous` — cada PIN reemplaza al anterior.
      Cubre: R2, R3, R4, R5.

- [x] T15 — Tests unitarios para parser `_parse_reset_command()`:
      - `test_parse_reset_command_basic` — "reset password juan" → "juan".
      - `test_parse_reset_command_case_insensitive` — case-insensitive.
      - `test_parse_reset_command_extra_spaces` — espacios extra tolerados.
      - `test_parse_reset_command_not_matching` — "hello world" → None.
      - `test_parse_reset_command_partial_no_username` — sin username → None.
      - `test_parse_reset_command_manual_on_not_matching` — "manual on" → None.
      - `test_parse_reset_command_multiple_spaces` — múltiples espacios.
      - `test_parse_reset_command_username_with_special_chars` — caracteres especiales.
      Cubre: R1.

- [x] T16 — Tests de integración para `POST /api/auth/verify-reset-pin`:
      - `test_verify_pin_success` — PIN correcto → reset_token.
      - `test_verify_pin_wrong` — PIN incorrecto → 401.
      - `test_verify_pin_no_user` — username no existe → 401.
      - `test_verify_pin_no_pin_set` — reset_pin=NULL → 401.
      - `test_verify_pin_expired` — PIN expirado → 401.
      - `test_verify_pin_already_used` — PIN ya usado → 401.
      - `test_verify_pin_case_insensitive_username` — búsqueda case-insensitive.
      - `test_verify_pin_short_pin` / `test_verify_pin_long_pin` — validación de longitud.
      Cubre: R7, R8, R9.

- [x] T17 — Tests de integración para `POST /api/auth/complete-reset`:
      - `test_complete_reset_success` — contraseña actualizada.
      - `test_complete_reset_invalid_token` — token inválido → 401.
      - `test_complete_reset_expired_token` — token expirado → 401.
      - `test_complete_reset_mismatch` — passwords no coinciden → 422.
      - `test_complete_reset_clears_force_password_change` — flag a False.
      - `test_complete_reset_clears_reset_fields` — campos NULL tras completar.
      - `test_complete_reset_empty_password` — validación min_length=1.
      - `test_complete_reset_prevents_login_with_old_password` — verificación end-to-end.
      Cubre: R10, R11, R12.

- [x] T18 — Tests para dispatcher `IncomingSmsDispatcher`:
      - `test_register_and_dispatch` — handler recibe SMS.
      - `test_handler_returns_true_stops_chain` — primer handler previene segundo.
      - `test_handler_returns_false_continues_chain` — False permite continuar.
      - `test_dev_mode_queue` — cola interna en dev mode.
      - `test_handler_exception_does_not_crash_dispatcher` — excepción no crashea.
      Cubre: R1 (infraestructura).

- [x] T19 — Tests para endpoints de usuarios:
      - `test_user_list_hides_reset_pin` — GET /api/users no incluye reset_pin.
      - `test_user_get_hides_reset_fields` — GET /api/users/{id} no incluye campos sensibles.
      - `test_user_response_includes_force_password_change` — force_password_change visible.
      Cubre: R14.

---

## Resumen de trazabilidad

| R  | Tareas que lo cubren | Tests implementados              |
|----|----------------------|----------------------------------|
| R1 | T4, T6, T15, T18     | test_parse_reset_command_*, test_dispatcher |
| R2 | T6, T14              | test_generate_pin_no_user        |
| R3 | T6, T14              | test_generate_pin_no_phone       |
| R4 | T6, T7, T14          | test_generate_pin_range          |
| R5 | T6, T7, T14          | test_generate_pin_hash_stored, test_generate_pin_expires_at, test_generate_pin_force_password_change |
| R6 | T6, T7               | test_generate_pin_range (verifica SMS enviado) |
| R7 | T9, T16              | test_verify_pin_success          |
| R8 | T8, T9, T16          | test_verify_pin_success (verifica reset_token emitido) |
| R9 | T9, T16              | test_verify_pin_wrong, test_verify_pin_no_user, test_verify_pin_no_pin_set, test_verify_pin_expired, test_verify_pin_already_used |
| R10| T8, T10, T17         | test_complete_reset_success      |
| R11| T10, T17             | test_complete_reset_clears_force_password_change, test_complete_reset_clears_reset_fields |
| R12| T10, T17             | test_complete_reset_invalid_token, test_complete_reset_expired_token, test_complete_reset_mismatch |
| R13| T1, T2               | (verificado: SQL migration + modelo SQLAlchemy con 3 columnas nuevas) |
| R14| T3, T19              | test_user_list_hides_reset_pin, test_user_get_hides_reset_fields, test_user_response_includes_force_password_change |
| R15| T4, T11, T12         | Página /login con modal de PIN (verificación manual + infraestructura dispatcher) |
| R16| T13                  | Modal de cambio de contraseña en página /login (verificación manual) |
