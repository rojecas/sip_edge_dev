# Review — feature 9 (emergency_mode)

**Veredicto:** CHANGES_REQUESTED

---

## Trazabilidad requirements <-> tests

| R<n> | Estado | Test(s) | Notas |
|------|--------|---------|-------|
| R1 | [x] | `TestEmergencyModeAPI.test_create_request_returns_200` | |
| R2 | [x] | `TestEmergencyModeAPI.test_get_admins_returns_list` | |
| R3 | [x] | `TestEmergencyModeService.test_create_request_empty_motivo`, `TestEmergencyModeService.test_create_request_whitespace_motivo`, `TestEmergencyModeAPI.test_create_request_empty_motivo` | |
| R4 | [x] | `TestEmergencyModeService.test_create_request_sends_sms` | |
| R5 | [x] | `TestEmergencyModeService.test_multiple_requests_first_wins` | |
| R6 | [x] | `TestSmsParser.test_parse_manual_on`, `TestEmergencyModeService.test_activate_default_duration`, `TestSmsPolling.test_incoming_sms_activate` | |
| R7 | [x] | `TestSmsParser.test_parse_manual_on_4h`, `TestSmsParser.test_parse_manual_on_30m`, `TestEmergencyModeService.test_activate_custom_duration` | |
| R8 | [x] | `TestSmsParser.test_parse_manual_on_ext_2h`, `TestSmsParser.test_parse_manual_on_ext_45m`, `TestEmergencyModeService.test_extend_active`, `TestSmsPolling.test_incoming_sms_extend` | |
| R9 | [x] | `TestSmsParser.test_parse_manual_off`, `TestEmergencyModeService.test_deactivate`, `TestSmsPolling.test_incoming_sms_deactivate` | |
| R10 | [x] | `TestEmergencyModeService.test_auto_expire_sets_inactive` | La expiracion automatica se prueba mediante llamada directa a `deactivate()`, no mediante el loop asyncio. Aceptable porque el loop solo envuelve a `deactivate()`. |
| R11 | [x] | `TestEmergencyModeService.test_direct_activation_no_prior_request`, `TestSmsPolling.test_incoming_sms_activate` | |
| R12 | [x] | `TestEmergencyModeService.test_reactivate_while_active_renews_timer` | |
| R13 | [x] | `TestEmergencyModeAPI.test_get_status_returns_active_false_initially`, `TestEmergencyModeAPI.test_get_status_active_after_activation` | |
| R14 | [x] | `TestEmergencyModeService.test_restore_from_db_active`, `TestEmergencyModeService.test_restore_from_db_expired` | |
| R15 | [x] | `TestEmergencyModeService.test_activation_creates_audit_log`, `TestEmergencyModeService.test_deactivation_creates_audit_log`, `TestEmergencyModeService.test_extension_creates_audit_log` | |
| R16 | [x] | `TestSmsParser.test_parse_invalid_gibberish`, `TestSmsParser.test_parse_invalid_partial`, `TestSmsParser.test_parse_invalid_zero_duration`, `TestSmsPolling.test_incoming_sms_invalid_command` | |
| R17 | [x] | `TestSmsPolling.test_incoming_sms_unauthorized_sender`, `TestSmsPolling.test_incoming_sms_unknown_sender` | |
| **R18** | **[ ]** | `TestEmergencyModeService.test_direct_activation_no_prior_request` | **FALLA**: el test mapeado cubre R11 (activacion directa sin solicitud previa), NO R18. R18 exige verificar que CUANDO existe una solicitud previa, la activacion se vincule mediante `request_id`. El test `test_direct_activation_no_prior_request` verifica lo opuesto. No hay ningun test que pase un `request_id` no-None a `activate()` y verifique el vinculo. |
| R19 | [x] | `TestEmergencyModeService.test_extend_inactive_raises`, `TestSmsPolling.test_incoming_sms_extend_when_inactive` | |

**Conclusion trazabilidad:** 18/19 R<n> cubiertos. R18 carece de test que verifique el escenario requerido.

---

## Tasks completas

| Task | Estado | Notas |
|------|--------|-------|
| T1-T19 | [x] | Completadas |
| T20 | [ ] | Verificacion en EdgeBox pendiente. Justificacion documentada en `impl_emergency_mode.md` y `tasks.md`. |

**Problema:** T20 esta `[ ]` y, aunque hay justificacion, `harness/docs/verification.md` establece que el Nivel 4 (EdgeBox) es **OBLIGATORIO** para features que toquen hardware (modem GSM). Esta feature depende de `sms_service` y usa `mmcli` para polling. No se puede declarar `done` sin T20 completo.

---

## GitHub sync

- `harness/github.json`: `"enabled": true`
- **[ ] Feature #9 NO tiene campo `github_issue` en `feature_list.json`.**
- El protocolo S4 de `AGENTS.md` dice: "Si `harness/github.json` tiene `enabled: true`, el leader DEBE crear el issue al transicionar a `in_progress`."
- Todas las features previas (1-7, 10) tienen `github_issue`. La #9 no.

---

## Arquitectura y convenciones

### Hallazgo 1: Indice compuesto faltante en `models.py`

- `design.md` seccion Persistencia especifica: `Indices: (status, expires_at)` para busqueda rapida de registros activos y expiracion.
- `database/migrations/2026_06_16_000001_create_emergency_mode_log.sql` linea 20: `INDEX idx_eml_status_expires (status, expires_at)` — correcto.
- `src/models.py` clase `EmergencyModeLog` (lineas 96-151): **NO define el indice compuesto** `(status, expires_at)`. Solo tiene indices individuales via `index=True` en `request_id`, `analyst_id`, `supervisor_id`.
- Consecuencia: el entorno de tests (SQLite via `create_all()`) no tendra el indice, mientras que produccion (MariaDB via migration) si. Inconsistencia entre spec, migracion y modelo ORM.

### Hallazgo 2: Test con nombre/documentacion enganosa

- `tests/test_emergency_mode.py` lineas 99-104: `test_parse_invalid_extra_spaces` tiene docstring que dice "texto con espacios extra detectado como invalid" pero la asercion verifica `self.assertEqual(result.action, "activate")`. El comportamiento es correcto (los espacios se manejan bien), pero el nombre y docstring del test son enganosos.

### Conformidad general

- **Capas:** `src/emergency_mode.py` orquesta parser + servicio + router en un solo archivo. Diseno documentado en `design.md`. Consistente con el patron del proyecto (ej. `src/weighings.py`). Aceptable.
- **Dependencias externas:** Solo usa FastAPI, Pydantic, SQLAlchemy — dependencias ya existentes. OK.
- **Errores explicitos:** Excepciones nombradas (`EmergencyModeError`, `InvalidSmsCommandError`, `UnauthorizedSenderError`). OK.
- **Inmutabilidad:** `ParsedSmsCommand` es `@dataclass(frozen=True)`. OK.
- **Convenciones PEP 8:** Lineas < 100 chars (verificado). Imports correctos. Strings con comillas dobles. Nombres snake_case/PascalCase correctos. OK.
- **SOLID:** SRP — el modulo en un solo archivo es consistente con el diseno acordado. DIP — depende de `db_session_factory` (callable) y `sms_service` (duck typing). Aceptable.

---

## Tests

- 53/53 tests especificos de `emergency_mode` pasan (verificado).
- Tests existentes de otras features: todos `ok` en ejecucion parcial.
- `./init.ps1`: timeout en seccion 6 (tests) pero todos los checks estructurales `[OK]`.

---

## Checkpoints

- C1: [x] harness completo
- C2: [ ] — `github_issue` ausente para feature #9
- C3: [x] codigo respeta arquitectura (ver hallazgos menores arriba)
- C4: [x] tests existen y pasan
- C5: [ ] — indice compuesto `(status, expires_at)` ausente en modelo ORM
- C6: [x] sesion documentada
- C7: [ ] — R18 sin cobertura de test
- C8: [x] closure existe y documenta decisiones
- C10: [ ] — feature sin `github_issue` (github habilitado)
- C11: [x] No aplica (bug)

---

## Release

- [ ] La feature NO esta lista para release-manager. Requiere:
  1. Anadir test que cubra R18 (vinculacion `request_id` en activacion con solicitud previa).
  2. Anadir indice compuesto `(status, expires_at)` al modelo `EmergencyModeLog` en `src/models.py`.
  3. Agregar campo `github_issue` en `feature_list.json` para la feature #9 y crear el issue en GitHub.
  4. Completar T20 (verificacion EdgeBox Nivel 4) antes de marcar `done`.
  5. Corregir nombre/docstring de `test_parse_invalid_extra_spaces`.

---

## Cambios requeridos

1. **R18 — Anadir test** que cree una solicitud y luego active con `request_id` no-None, verificando que el registro de activacion tenga `request_id` apuntando a la solicitud original.
2. **Indice compuesto** — Anadir `Index("idx_eml_status_expires", "status", "expires_at")` en `__table_args__` de `EmergencyModeLog` en `src/models.py`.
3. **GitHub issue** — Agregar `"github_issue": "https://github.com/rojecas/sip_edge/issues/9"` (o el numero que corresponda) en `harness/feature_list.json` para feature #9.
4. **T20** — Completar verificacion en EdgeBox (Nivel 4 obligatorio por `verification.md`).
5. **Test name** — Renombrar `test_parse_invalid_extra_spaces` a `test_parse_extra_spaces_valid` y corregir docstring.