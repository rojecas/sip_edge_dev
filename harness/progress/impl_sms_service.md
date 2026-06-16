# Implementacion — sms_service (Feature 7)

> Fecha: 2026-06-15  
> Agente: implementer  
> Estado: in_progress → pending review

---

## Trazabilidad

| Requirement | Descripcion | Test(s) |
|-------------|-------------|---------|
| R1 | Envio de SMS (dual dev/prod) | `TestSMSServiceDevMode.test_send_sms_simulates_and_returns_true`, `TestSMSServiceDevMode.test_send_sms_empty_phone_returns_false`, `TestSMSServiceDevMode.test_send_sms_empty_message_returns_false`, `TestSMSServiceDevMode.test_send_alert_to_admins_sends_to_all`, `TestSMSServiceProdMode.test_send_sms_calls_mmcli_create_and_send` |
| R2 | Alerta por 3+ intentos fallidos de login | `TestLoginFailedAttempts.test_login_failed_triggers_alert_at_3`, `TestLoginFailedAttempts.test_login_failed_does_not_alert_before_3` |
| R3 | Contador de intentos fallidos por usuario | `TestLoginFailedAttempts.test_login_failed_increments_counter`, `TestLoginFailedAttempts.test_login_success_resets_counter`, `TestLoginFailedAttempts.test_login_failed_counter_increments_separately_per_user` |
| R4 | Reseteo del contador tras alerta | `TestLoginFailedAttempts.test_login_failed_resets_after_alert`, `TestLoginFailedAttempts.test_login_failed_triggers_alert_only_once_per_batch` |
| R5 | Reporte programado de turno | `TestSchedulerBehavior.test_scheduler_sends_report_at_scheduled_time`, `TestSchedulerBehavior.test_scheduler_does_not_send_when_no_match` |
| R6 | Configuracion de horarios de reporte | `TestLoadSaveConfig.test_load_defaults_when_no_file` (verifica defaults), `TestLoadSaveConfig.test_save_and_load_roundtrip` (verifica persistencia) |
| R7 | Configuracion de numeros de administrador | `TestSMSServiceEmptyPhones.test_send_alert_does_nothing_with_empty_phones`, `TestSMSServiceEmptyPhones.test_send_scheduled_report_does_nothing_with_empty_phones` |
| R8 | Tolerancia a fallos en envio de SMS | `TestSMSServiceErrorHandling.test_send_sms_returns_false_when_create_fails`, `TestSMSServiceErrorHandling.test_send_sms_returns_false_when_send_fails`, `TestSMSServiceErrorHandling.test_send_sms_returns_false_when_no_sms_index_in_output`, `TestSMSServiceErrorHandling.test_send_sms_handles_subprocess_timeout`, `TestSMSServiceErrorHandling.test_send_sms_handles_file_not_found`, `TestSMSServiceErrorHandling.test_send_to_admins_continues_after_individual_failure` |
| R9 | Modo desarrollo (simulacion sin modem) | `TestSMSServiceDevMode.test_send_sms_simulates_and_returns_true` |
| R10 | Carga de configuracion SMS al iniciar | Verificado por T5 (lifespan carga SmsConfig). Cobertura indirecta via `load_config()` tests. |
| R11 | Contenido del reporte de turno | `TestGenerateTurnReport.test_generate_turn_report_includes_period_count_and_weight`, `TestGenerateTurnReport.test_generate_turn_report_empty_range_returns_zero`, `TestGenerateTurnReport.test_generate_turn_report_period_is_configurable` |
| R12 | Prevencion de envios duplicados de reporte | `TestSchedulerBehavior.test_scheduler_does_not_duplicate_report_same_slot`, `TestSchedulerBehavior.test_scheduler_resets_sent_today_on_new_day` |

---

## Archivos creados

| Archivo | Proposito |
|---------|-----------|
| `src/sms_service.py` | Clase SMSService, SMSDeliveryError, logica dual dev/prod, planificador asyncio |
| `tests/test_sms_service.py` | 22 tests unitarios del SMSService (15 originales + 7 anadidos por reviewer feedback: R5, R11, R12) |
| `database/migrations/2026_06_15_000001_add_failed_login_attempts_to_users.sql` | Migracion SQL para produccion |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | Anadida columna `failed_login_attempts` a `User` |
| `src/config.py` | Anadido dataclass `SmsConfig`, extendido `load_config()` (5-tuple), `save_sms_config()`, `_atomic_write_sections()`, `_save_system_config_atomic()` |
| `src/main.py` | Modificado `POST /api/auth/login` para contador + alerta; modificado lifespan para SMSService |
| `tests/test_auth.py` | Anadida clase `TestLoginFailedAttempts` con 7 tests |
| `tests/test_config.py` | Actualizados 5 unpackings de `load_config()` (4-tuple → 5-tuple) |
| `tests/test_scale.py` | Actualizados 4 unpackings de `load_config()` (4-tuple → 5-tuple) |
| `tests/test_backup.py` | Actualizados 3 unpackings de `load_config()` (4-tuple → 5-tuple) |

---

## Decisiones tecnicas

1. **Envio SMS via mmcli**: Se usa `subprocess.run()` con dos pasos:
   `mmcli -m <index> --messaging-create-sms="number=...,text=..."` seguido de
   `mmcli -s <sms_index> --send`, como documenta el design.md.

2. **Planificador asyncio**: Se implementa con `asyncio.create_task()` y un bucle
   que verifica cada 30 segundos. Se usa un `set` para evitar duplicados en el
   mismo dia, reseteado cada medianoche UTC.

3. **Ventana de turno**: Se mapean los horarios por defecto (06:00 → turno
   00:00-06:00, 14:00 → turno 06:00-14:00, 22:00 → turno 14:00-22:00). Para
   horarios personalizados, se usa el horario inmediatamente anterior.

4. **Tolerancia a fallos**: Cada `send_sms` captura excepciones y retorna `bool`.
   `send_alert_to_admins` y `send_scheduled_report` iteran sobre los phones
   sin interrumpirse si un envio individual falla.

---

## Verificacion

```bash
# Tests unitarios del SMSService (22 tests: 15 originales + 7 nuevos)
docker compose exec backend python -m unittest tests.test_sms_service -v
# Resultado: 22 tests OK

# Tests de auth (incluye tests de intentos fallidos)
docker compose exec backend python -m unittest tests.test_auth -v
# Resultado: 37 tests OK (7 nuevos + 30 existentes)

# Tests de config (corregidos por nuevo return type)
docker compose exec backend python -m unittest tests.test_config -v
# Resultado: 20 tests OK

# Tests de scale (corregidos por nuevo return type)
docker compose exec backend python -m unittest tests.test_scale -v
# Resultado: 30 tests OK

# Tests de backup (corregidos por nuevo return type)
docker compose exec backend python -m unittest tests.test_backup -v
# Resultado: 23 tests OK

# Tests de weighing
docker compose exec backend python -m unittest tests.test_weighings -v
# Resultado: 115 tests OK, 1 ERROR (pre-existente: RuntimeError event loop en websocket test)
```
