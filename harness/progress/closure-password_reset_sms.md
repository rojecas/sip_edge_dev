# Cierre — password_reset_sms

## Resumen

Se implementó el restablecimiento remoto de contraseña vía SMS para la Feature #12.
El administrador envía un comando SMS `"reset password <username>"` al sistema;
SIP-Edge genera un PIN numérico de 4 dígitos, válido por 1 hora y de un solo uso,
y lo envía por SMS al teléfono registrado del analista. En la pantalla de login,
el enlace "Olvidó su contraseña" permite ingresar usuario + PIN para acceder a
un modal de cambio de contraseña.

Se refactorizó el polling de SMS entrantes: se creó `IncomingSmsDispatcher` compartido
que reemplaza el polling duplicado en `EmergencyModeService`, resolviendo condiciones
de carrera entre features que reciben SMS (emergency_mode y password_reset).

## Archivos modificados

| Archivo | Acción | Cambio |
|---------|--------|--------|
| `database/migrations/2026_06_16_000003_add_password_reset_fields.sql` | Creado | Migración: agrega `force_password_change`, `reset_pin`, `reset_pin_expires_at` a `users` |
| `src/models.py` | Modificado | Agregadas 3 columnas al modelo `User` (force_password_change, reset_pin, reset_pin_expires_at) |
| `src/users.py` | Modificado | `UserResponse`: agregado `force_password_change`, excluidos campos sensibles `reset_pin` y `reset_pin_expires_at` |
| `src/auth.py` | Modificado | Agregados `create_reset_token()` y `decode_reset_token()` para JWT de reset con expiración de 5 min |
| `src/emergency_mode.py` | Modificado | Refactorizado: eliminado polling SMS propio; `process_incoming_sms` ahora retorna `bool` |
| `src/main.py` | Modificado | Inicialización de `IncomingSmsDispatcher`, `PasswordResetService`, registro de routers y handlers |
| `src/sms_incoming.py` | Creado | Nuevo dispatcher compartido de SMS entrantes con `IncomingSmsDispatcher` |
| `src/password_reset.py` | Creado | Servicio de reset, parser SMS, schemas Pydantic, endpoints API |
| `src/login_page.py` | Creado | Página HTML de login con modales de restablecimiento de contraseña |
| `tests/test_password_reset.py` | Creado | 51 tests unitarios y de integración |
| `tests/test_emergency_mode.py` | Modificado | Actualizado test para reflejar nuevo comportamiento del handler |
| `harness/specs/12_password_reset_sms/tasks.md` | Modificado | Todas las 19 tasks marcadas `[x]` |

## Decisiones técnicas

1. **Dispatcher compartido:** Se creó `IncomingSmsDispatcher` en `src/sms_incoming.py` para centralizar el polling mmcli, eliminando el polling duplicado que existía en `EmergencyModeService`. Los handlers se registran en orden: primero emergency, luego password_reset. Si un handler retorna `True`, los siguientes no se ejecutan.

2. **`process_incoming_sms` refactorizado a retorno `bool`:** Se modificó para que primero evalúe si el texto coincide con un patrón de emergencia; si no, retorna `False` inmediatamente sin verificar el emisor, permitiendo que el handler de password reset lo procese.

3. **Seguridad del PIN:** Almacenado con hash bcrypt (no texto plano). Reset token JWT con expiración de 5 minutos. Mensajes de error genéricos ("Invalid username or PIN") para no revelar información. Single-use: PIN se invalida tras verificación exitosa.

4. **Frontend sin Jinja2:** La página de login se implementó con `HTMLResponse` e inline HTML/CSS/JS para evitar agregar dependencias externas.

5. **Alternativa descartada — PIN en texto plano:** Se descartó almacenar el PIN sin hash. Cualquier leak de la BD expondría todos los PINs activos. El costo de bcrypt es negligible (10,000 combinaciones) comparado con el beneficio de seguridad.

## Verificación

- [x] `./init.ps1` verde — todos los bloques `[OK]`
- [x] 51 tests en `tests/test_password_reset.py` — OK
- [x] Tests existentes en `tests/test_emergency_mode.py` — OK (sin regresiones)
- [x] Suite completa: 362 tests totales, sin regresiones

### Trazabilidad R<n> ↔ tests

| R | Tests |
|---|-------|
| R1 — Recepción comando SMS | `test_parse_reset_command_*` (8 tests), `test_register_and_dispatch` |
| R2 — Usuario no existe | `test_generate_pin_no_user` |
| R3 — Usuario sin teléfono | `test_generate_pin_no_phone` |
| R4 — Generación PIN 4 dígitos | `test_generate_pin_range` |
| R5 — Persistencia del PIN | `test_generate_pin_hash_stored`, `test_generate_pin_expires_at`, `test_generate_pin_force_password_change`, `test_generate_pin_multiple_generations_invalidate_previous` |
| R6 — Envío PIN por SMS | `test_generate_pin_range` (verifica SMS enviado al teléfono) |
| R7 — Endpoint verify-reset-pin | `test_verify_pin_success` |
| R8 — Emisión reset_token JWT | `test_verify_pin_success` (verifica reset_token), `test_verify_pin_already_used` (single-use) |
| R9 — Rechazo PIN inválido | `test_verify_pin_wrong`, `test_verify_pin_no_user`, `test_verify_pin_no_pin_set`, `test_verify_pin_expired`, `test_verify_pin_already_used` |
| R10 — Endpoint complete-reset | `test_complete_reset_success` |
| R11 — Actualización contraseña | `test_complete_reset_success`, `test_complete_reset_clears_force_password_change`, `test_complete_reset_clears_reset_fields`, `test_complete_reset_prevents_login_with_old_password` |
| R12 — Rechazo cambio inválido | `test_complete_reset_invalid_token`, `test_complete_reset_expired_token`, `test_complete_reset_mismatch` |
| R13 — Columnas BD | Migración SQL + modelo SQLAlchemy con 3 columnas nuevas |
| R14 — Protección campos sensibles | `test_user_list_hides_reset_pin`, `test_user_get_hides_reset_fields`, `test_user_response_includes_force_password_change` |
| R15 — Enlace "Olvidó su contraseña" | `test_login_page_has_forgot_password_link_and_pin_modal` |
| R16 — Modal cambio contraseña | `test_login_page_has_password_modal_with_fields` |

## Lecciones / pitfalls

- La migración SQL se nombró `2026_06_16_000003` porque ya existían migraciones con `000001` y `000002`. Verificar el orden de migraciones existentes antes de crear una nueva.
- La refactorización del dispatcher SMS fue necesaria para evitar condiciones de carrera entre features #9 y #12. Es recomendable diseñar el dispatcher compartido desde el inicio para futuras features que reciban SMS.
- Los tests de la página de login (R15 y R16) se agregaron en re-evaluación del reviewer. Verificar siempre cobertura de tests de frontend HTML cuando se sirven páginas.
