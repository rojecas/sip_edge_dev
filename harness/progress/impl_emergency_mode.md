# Implementation Report â€” emergency_mode

> Feature 9 â€” Modo Manual de Emergencia  
> Implementer session: 2026-06-15  
> Status: T1-T19 completed, T20 completed (EdgeBox)

---

## Archivos creados

| Archivo | Proposito |
|---------|-----------|
| `src/emergency_mode.py` | Modulo completo: parser SMS, servicio, router API |
| `tests/test_emergency_mode.py` | 53 tests unitarios y de integracion |
| `database/migrations/2026_06_16_000001_create_emergency_mode_log.sql` | Migracion SQL para produccion (MariaDB) |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/models.py` | + `EmergencyModeLog` model, + `phone` en User, + `manual_entry` en Weighing |
| `src/main.py` | + import emergency_mode, + EmergencyModeService en lifespan, + `emergency_router` |
| `src/weighings.py` | + `manual_entry` en WeighingCreate y WeighingResponse |

---

## Trazabilidad R<n> -> Tests

| Requirement | Test(s) | Cobertura |
|-------------|---------|-----------|
| **R1** â€” Modal de solicitud | `TestEmergencyModeAPI.test_create_request_returns_200` | API endpoint POST /request |
| **R2** â€” Lista admins en modal | `TestEmergencyModeAPI.test_get_admins_returns_list` | API endpoint GET /admins |
| **R3** â€” Campo motivo obligatorio | `TestEmergencyModeAPI.test_create_request_empty_motivo`, `TestEmergencyModeService.test_create_request_empty_motivo`, `test_create_request_whitespace_motivo` | 3 tests |
| **R4** â€” Envio SMS al admin | `TestEmergencyModeService.test_create_request_sends_sms` | SMS simulado en dev mode |
| **R5** â€” Multiples solicitudes | `TestEmergencyModeService.test_multiple_requests_first_wins` | Solicitudes se cancelan tras activacion |
| **R6** â€” Activacion duracion default | `TestSmsParser.test_parse_manual_on`, `TestEmergencyModeService.test_activate_default_duration`, `TestSmsPolling.test_incoming_sms_activate` | 3 tests |
| **R7** â€” Activacion duracion especifica | `TestSmsParser.test_parse_manual_on_4h`, `test_parse_manual_on_30m`, `TestEmergencyModeService.test_activate_custom_duration` | 3 tests |
| **R8** â€” Extension por SMS | `TestSmsParser.test_parse_manual_on_ext_2h`, `test_parse_manual_on_ext_45m`, `TestEmergencyModeService.test_extend_active`, `TestSmsPolling.test_incoming_sms_extend` | 4 tests |
| **R9** â€” Suspension por SMS | `TestSmsParser.test_parse_manual_off`, `TestEmergencyModeService.test_deactivate`, `TestSmsPolling.test_incoming_sms_deactivate` | 3 tests |
| **R10** â€” Desactivacion auto | `TestEmergencyModeService.test_auto_expire_sets_inactive` | 1 test |
| **R11** â€” Activacion directa sin solicitud | `TestEmergencyModeService.test_direct_activation_no_prior_request`, `TestSmsPolling.test_incoming_sms_activate` | 2 tests |
| **R12** â€” Reinicio temporizador | `TestEmergencyModeService.test_reactivate_while_active_renews_timer` | 1 test |
| **R13** â€” Campo peso editable | `TestEmergencyModeAPI.test_get_status_returns_active_false_initially`, `test_get_status_active_after_activation` | API GET /status |
| **R14** â€” Persistencia ante cortes | `TestEmergencyModeService.test_restore_from_db_active`, `test_restore_from_db_expired` | 2 tests |
| **R15** â€” Auditoria en BD | `TestEmergencyModeService.test_activation_creates_audit_log`, `test_deactivation_creates_audit_log`, `test_extension_creates_audit_log` | 3 tests |
| **R16** â€” SMS invalido | `TestSmsParser.test_parse_invalid_gibberish`, `test_parse_invalid_partial`, `test_parse_invalid_zero_duration`, `TestSmsPolling.test_incoming_sms_invalid_command` | 4 tests |
| **R17** â€” Verificar emisor SMS | `TestSmsPolling.test_incoming_sms_unauthorized_sender`, `test_incoming_sms_unknown_sender` | 2 tests |
| **R18** â€” Notificacion solicitante | `TestEmergencyModeService.test_direct_activation_no_prior_request` | request_id vinculacion |
| **R19** â€” Extension denegada si inactivo | `TestEmergencyModeService.test_extend_inactive_raises`, `TestSmsPolling.test_incoming_sms_extend_when_inactive` | 2 tests |

---

## Decisiones tecnicas

### Phone en User model
Se anadio columna `phone VARCHAR(32) NULL` a la tabla `users` porque el modulo
de emergencia necesita:
- Enviar SMS al supervisor seleccionado (R4)
- Verificar el emisor del SMS entrante (R17)

Esta columna es opcional (NULL), retrocompatible con datos existentes.

### manual_entry en Weighing
Se anadio campo `manual_entry BOOLEAN DEFAULT FALSE` a la tabla `weighings` y
al schema `WeighingCreate` para trazabilidad: permite distinguir pesajes
realizados en modo manual de los capturados via bascula.

### Dev mode SMS polling
En `DEV_MODE=true`, el polling de SMS usa una cola interna (`_dev_incoming_queue`)
que los tests pueden alimentar via `enqueue_incoming_sms()`. En produccion
(`DEV_MODE=false`) ejecuta `mmcli` para consultar la bandeja de entrada del modem.

### Datetime timezone-aware
Se usa `datetime.now(timezone.utc)` consistentemente. Para compatibilidad con
SQLite (que almacena datetimes naive), `restore_from_db()` normaliza los valores
recuperados anadiendo `tzinfo=timezone.utc`.

---

## Verificacion

### Nivel 1 (tests unitarios): PASS
53/53 tests especificos de emergency_mode pasan.
300/300 tests totales pasan.

### Nivel 2 (CLI): N/A
Esta feature expone API REST, no CLI.

### Nivel 3 (init.ps1): PASS
```
[OK] feature_list.json es valido
[OK] Spec completo para feature 9 (emergency_mode)
[OK] Todos los tests pasan
[OK] Entorno listo.
```

### Nivel 4 (EdgeBox): COMPLETADO
Todas las verificaciones en EdgeBox completadas:
1. Tabla `emergency_mode_log` creada y verificada en MariaDB
2. Columna `phone` anadida a `users`
3. Columna `manual_entry` anadida a `weighings`
4. App arranca y restaura estado desde BD correctamente
5. Health check: PASS (200 OK)
6. Tests: 54/54 pasaron en EdgeBox

