# Implementation Report — password_reset_sms (Feature #12)

> **Fecha:** 2026-06-16
> **Agente:** implementer
> **Estado:** Implementación completada, tests OK

---

## Archivos modificados

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `database/migrations/2026_06_16_000003_add_password_reset_fields.sql` | Creado | Migración: agrega `force_password_change`, `reset_pin`, `reset_pin_expires_at` a `users` |
| `src/models.py` | Modificado | Agregadas 3 columnas al modelo `User` |
| `src/users.py` | Modificado | `UserResponse`: agregado `force_password_change`, excluidos `reset_pin` y `reset_pin_expires_at` |
| `src/auth.py` | Modificado | Agregados `create_reset_token()` y `decode_reset_token()` |
| `src/emergency_mode.py` | Modificado | Refactorizado: eliminado polling SMS propio, `process_incoming_sms` ahora retorna `bool` |
| `src/main.py` | Modificado | Inicialización de `IncomingSmsDispatcher`, `PasswordResetService`, registro de routers y handlers |
| `src/sms_incoming.py` | Creado | Nuevo dispatcher compartido de SMS entrantes con `IncomingSmsDispatcher` |
| `src/password_reset.py` | Creado | Servicio de reset, parser SMS, schemas Pydantic, endpoints API |
| `src/login_page.py` | Creado | Página HTML de login con modales de restablecimiento |
| `tests/test_password_reset.py` | Creado | 49 tests unitarios y de integración |
| `tests/test_emergency_mode.py` | Modificado | Actualizado 1 test para reflejar nuevo comportamiento del handler |
| `harness/specs/12_password_reset_sms/tasks.md` | Modificado | Todas las 19 tasks marcadas `[x]` |

---

## Trazabilidad R → Tests

| Requirement | Test(s) |
|-------------|---------|
| R1 — Recepción comando SMS | `test_parse_reset_command_basic`, `test_parse_reset_command_case_insensitive`, `test_parse_reset_command_extra_spaces`, `test_parse_reset_command_not_matching`, `test_parse_reset_command_partial_no_username`, `test_parse_reset_command_manual_on_not_matching`, `test_parse_reset_command_multiple_spaces`, `test_parse_reset_command_username_with_special_chars`, `test_register_and_dispatch` |
| R2 — Usuario no existe | `test_generate_pin_no_user` |
| R3 — Usuario sin teléfono | `test_generate_pin_no_phone` |
| R4 — Generación PIN 4 dígitos | `test_generate_pin_range` |
| R5 — Persistencia del PIN | `test_generate_pin_hash_stored`, `test_generate_pin_expires_at`, `test_generate_pin_force_password_change`, `test_generate_pin_multiple_generations_invalidate_previous` |
| R6 — Envío PIN por SMS | `test_generate_pin_range` (verifica `sms_service.send_sms` llamado) |
| R7 — Endpoint verify-reset-pin | `test_verify_pin_success` |
| R8 — Emisión reset_token JWT | `test_verify_pin_success` (verifica `reset_token` en respuesta), `test_verify_pin_already_used` (single-use) |
| R9 — Rechazo PIN inválido | `test_verify_pin_wrong`, `test_verify_pin_no_user`, `test_verify_pin_no_pin_set`, `test_verify_pin_expired`, `test_verify_pin_already_used` |
| R10 — Endpoint complete-reset | `test_complete_reset_success` |
| R11 — Actualización contraseña | `test_complete_reset_success`, `test_complete_reset_clears_force_password_change`, `test_complete_reset_clears_reset_fields`, `test_complete_reset_prevents_login_with_old_password` |
| R12 — Rechazo cambio inválido | `test_complete_reset_invalid_token`, `test_complete_reset_expired_token`, `test_complete_reset_mismatch` |
| R13 — Columnas BD | Migración SQL + modelo SQLAlchemy con 3 columnas nuevas |
| R14 — Protección campos sensibles | `test_user_list_hides_reset_pin`, `test_user_get_hides_reset_fields`, `test_user_response_includes_force_password_change` |
| R15 — Enlace "Olvidó su contraseña" | Página `/login` con modal de PIN (HTML+JS), infraestructura dispatcher y endpoints |
| R16 — Modal cambio contraseña | Página `/login` con modal de cambio de contraseña (HTML+JS), endpoint `POST /api/auth/complete-reset` |

---

## Decisiones técnicas

1. **Nombre de migración:** Se usó `2026_06_16_000003` en lugar de `000001` porque ya existían migraciones con `000001` y `000002`.

2. **Dispatcher compartido:** El `IncomingSmsDispatcher` centraliza el polling mmcli (antes duplicado en `EmergencyModeService`). El handler de emergencia se registra primero, luego el de password reset. Si un handler retorna `True`, los siguientes no se ejecutan.

3. **`process_incoming_sms` retorna `bool`:** Se refactorizó para que primero evalúe si el texto coincide con un patrón de emergencia. Si no coincide, retorna `False` inmediatamente (sin verificar emisor), permitiendo que el handler de password reset lo procese.

4. **`force_password_change` en `UserResponse`:** Se agregó explícitamente para que el frontend pueda saber si el usuario tiene un reset pendiente. Los campos `reset_pin` y `reset_pin_expires_at` se excluyen automáticamente al no estar declarados en el schema.

5. **Seguridad:** PIN almacenado con hash bcrypt (no texto plano). Reset token JWT con expiración de 5 minutos. Mensajes de error genéricos ("Invalid username or PIN") para no revelar información. Single-use: PIN se invalida tras verificación exitosa.

6. **Frontend sin Jinja2:** La página de login se implementó con `HTMLResponse` e inline HTML/CSS/JS para evitar agregar dependencias externas.

---

## Verificación

```
docker compose exec backend python -m unittest tests.test_password_reset -v
→ Ran 49 tests in ~24s — OK

docker compose exec backend python -m unittest tests.test_emergency_mode -v
→ Ran 55 tests in ~33s — OK
```

Total: **104 tests pasando** (49 nuevos + 55 existentes sin regresiones).

---

## Notas para el reviewer

- La página de login (`GET /login`) sirve HTML funcional con modales de restablecimiento. Verificar manualmente accediendo a `http://127.0.0.1:8000/login`.
- La migración SQL debe ejecutarse manualmente en producción: `mysql -u root -p sip_edge < database/migrations/2026_06_16_000003_add_password_reset_fields.sql`.
- Los endpoints de reset (`/api/auth/verify-reset-pin`, `/api/auth/complete-reset`) son públicos (sin autenticación previa), por diseño.
