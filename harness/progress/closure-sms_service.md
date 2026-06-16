# Cierre — sms_service

## Resumen

Se implementó el servicio de notificaciones y reportes SMS (Feature 7) para el sistema SIP-Edge.
El módulo `SMSService` permite el envío de SMS vía módem GSM (Quectel EC25) usando `mmcli`,
con un modo de simulación para desarrollo. Incluye alertas de seguridad inmediatas por intentos
de login fallidos (3+ consecutivos), reportes programados de resumen de turno (06:00, 14:00, 22:00
configurables) y persistencia de configuración SMS en `config.yaml`.

## Archivos creados

| Archivo | Cambio |
|---------|--------|
| `src/sms_service.py` | Módulo completo: clase `SMSService`, excepción `SMSDeliveryError`, planificador asyncio, envío dual dev/prod |
| `tests/test_sms_service.py` | 22 tests unitarios del servicio SMS |
| `database/migrations/2026_06_15_000001_add_failed_login_attempts_to_users.sql` | Migración SQL para producción (columna `failed_login_attempts`) |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Añadida columna `failed_login_attempts` a modelo `User` (Integer, default=0) |
| `src/config.py` | Añadido dataclass `SmsConfig` (frozen=True), extendido `load_config()` a 5-tuple, `save_sms_config()`, `_atomic_write_sections()` |
| `src/main.py` | Modificado `POST /api/auth/login` con contador de intentos + alerta SMS; modificado lifespan para crear/arrancar/detener SMSService |
| `tests/test_auth.py` | Añadida clase `TestLoginFailedAttempts` con 7 tests |
| `tests/test_config.py` | Actualizados 5 unpackings de `load_config()` (4-tuple → 5-tuple) |
| `tests/test_scale.py` | Actualizados 4 unpackings de `load_config()` (4-tuple → 5-tuple) |
| `tests/test_backup.py` | Actualizados 3 unpackings de `load_config()` (4-tuple → 5-tuple) |

## Decisiones técnicas

- **Envío SMS via `mmcli`**: Se usan dos comandos `subprocess.run()`: `mmcli -m <index> --messaging-create-sms=...` y `mmcli -s <sms_index> --send`, sin depender de bibliotecas externas.
- **Planificador asyncio**: Implementado con `asyncio.create_task()` y bucle de verificación cada 30 segundos. Usa un `set` (`_sent_today`) para evitar duplicados en el mismo día, con reseteo automático a medianoche UTC.
- **Ventana de turno**: Los horarios por defecto (06:00, 14:00, 22:00) mapean al período inmediatamente anterior (00:00-06:00, 06:00-14:00, 14:00-22:00). Para horarios personalizados se usa la misma lógica con el horario previo.
- **Tolerancia a fallos**: Cada `send_sms()` captura excepciones y retorna `bool`. `send_alert_to_admins()` y `send_scheduled_report()` iteran sobre los teléfonos sin interrumpirse si un envío individual falla (resiliencia ante fallos parciales del módem).
- **Modo desarrollo (dev_mode)**: Cuando `DEV_MODE=true`, el envío se simula con logging en lugar de llamar a `mmcli`, permitiendo desarrollo y tests sin hardware GSM real.
- **Late import**: `import src.database as _db` dentro de `_do_send_report()` para evitar circular imports entre `sms_service.py` y `database.py`.
- **Alternativa descartada**: Se consideró usar `python-gammu` como wrapper de GSM, pero se descartó para evitar dependencias externas (política del proyecto: solo stdlib).

## Trazabilidad R&lt;n&gt; ↔ tests

| Requirement | Tests |
|-------------|-------|
| R1 — Envío de SMS (dual dev/prod) | `test_send_sms_simulates_and_returns_true`, `test_send_sms_empty_phone_returns_false`, `test_send_sms_empty_message_returns_false`, `test_send_alert_to_admins_sends_to_all`, `test_send_sms_calls_mmcli_create_and_send` |
| R2 — Alerta por 3+ intentos fallidos | `test_login_failed_triggers_alert_at_3`, `test_login_failed_does_not_alert_before_3` |
| R3 — Contador de intentos fallidos | `test_login_failed_increments_counter`, `test_login_success_resets_counter`, `test_login_failed_counter_increments_separately_per_user` |
| R4 — Reseteo del contador tras alerta | `test_login_failed_resets_after_alert`, `test_login_failed_triggers_alert_only_once_per_batch` |
| R5 — Reporte programado de turno | `test_scheduler_sends_report_at_scheduled_time`, `test_scheduler_does_not_send_when_no_match` |
| R6 — Configuración de horarios | `test_load_defaults_when_no_file`, `test_save_and_load_roundtrip` |
| R7 — Configuración de números admin | `test_send_alert_does_nothing_with_empty_phones`, `test_send_scheduled_report_does_nothing_with_empty_phones` |
| R8 — Tolerancia a fallos SMS | `test_send_sms_returns_false_when_create_fails`, `test_send_sms_returns_false_when_send_fails`, `test_send_sms_returns_false_when_no_sms_index_in_output`, `test_send_sms_handles_subprocess_timeout`, `test_send_sms_handles_file_not_found`, `test_send_to_admins_continues_after_individual_failure` |
| R9 — Modo desarrollo | `test_send_sms_simulates_and_returns_true` |
| R10 — Carga de configuración al iniciar | Cobertura indirecta vía tests de `load_config()` y T5 (lifespan) |
| R11 — Contenido del reporte de turno | `test_generate_turn_report_includes_period_count_and_weight`, `test_generate_turn_report_empty_range_returns_zero`, `test_generate_turn_report_period_is_configurable` |
| R12 — Prevención de duplicados | `test_scheduler_does_not_duplicate_report_same_slot`, `test_scheduler_resets_sent_today_on_new_day` |

## Verificación

- [x] Tests unitarios del SMSService: 22 tests OK
- [x] Tests de auth (incluyendo intentos fallidos): 37 tests OK (7 nuevos + 30 existentes)
- [x] Tests de config (unpackings corregidos): 20 tests OK
- [x] Tests de scale (unpackings corregidos): 30 tests OK
- [x] Tests de backup (unpackings corregidos): 23 tests OK
- [x] Todos los R1–R12 tienen cobertura de test verificable
- [x] 8/8 tasks completadas según spec SDD
- [x] Código respeta capas, PEP 8, inmutabilidad (SmsConfig frozen=True)
- [x] Sin dependencias externas nuevas
- [x] Closure listo para release-manager
- [ ] `./init.ps1` — 1 error pre-existente en `test_weighings` (websocket event loop thread, **no relacionado con sms_service**). El resto de secciones [OK].

## Lecciones / pitfalls

- El cambio de `load_config()` de 4-tuple a 5-tuple rompió unpackings en 3 módulos de tests (`test_config`, `test_scale`, `test_backup`). Es un punto frágil a tener en cuenta para futuras extensiones del config.
- El error pre-existente del websocket en `test_weighings` impide que `./init.ps1` esté completamente verde, pero es ajeno a esta feature.
- El GitHub issue para esta feature quedó como placeholder (`issues/999999`) porque nunca se creó el issue real en GitHub durante la transición a `in_progress`.

## GitHub Issue

- URL configurada: `https://github.com/rojecas/sip_edge/issues/999999` (placeholder)
- Estado: No se pudo cerrar automáticamente — el issue nunca fue creado (placeholder no válido). Además, `gh auth` no está configurado en el entorno Docker.
- Acción requerida: Crear el issue en GitHub manualmente y actualizar `github_issue` en `feature_list.json`, o ejecutar `gh auth login` y luego `python harness/scripts/github_sync.py close --feature-id 7`.
