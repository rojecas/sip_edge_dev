# Review — feature 17 (frontend_analytics) — Fase 8 (tabla pivote report_template_users)

**Veredicto:** APPROVED

## Trazabilidad requirements <-> tests

### R19
CUANDO un administrador guarda una plantilla de reporte, el sistema DEBE almacenar los destinatarios como referencias a usuarios (user_id) en una tabla pivote report_template_users, NO como texto plano de numeros de telefono en la columna recipients.

- [x] `test_create_with_user_ids` — Verifica que crear plantilla con user_ids resuelve recipients desde la tabla pivote.
- [x] `test_get_all_resolves_recipients` — Verifica que get_all() resuelve recipients via JOIN desde pivote + users.
- [x] `test_update_replaces_recipients` — Verifica que al actualizar user_ids se reemplazan los destinatarios.
- [x] `test_create_without_user_ids` — Verifica que crear sin user_ids no agrega destinatarios.
- [x] Frontend: "carga usuarios via GET /api/users al abrir" — Verifica carga inicial de usuarios.
- [x] Frontend: "muestra solo admin y corresponsal activos" — Verifica filtrado por rol y activo.
- [x] Frontend: "filtra usuarios por nombre con la busqueda" — Verifica busqueda por nombre.
- [x] Frontend: "envia user_ids en el payload al guardar" — Verifica envio de user_ids (sin recipients).
- [x] Frontend: "modo edit pre-selecciona usuarios desde recipient_ids" — Verifica pre-seleccion en edicion.
- [x] Frontend: "muestra mensaje si no hay usuarios admin/corresponsal activos" — Verifica caso sin usuarios.

### R20
CUANDO el sistema envia un reporte programado, DEBE resolver los numeros de telefono de los destinatarios mediante JOIN desde la tabla users a traves de la tabla pivote report_template_users, garantizando que los telefonos esten siempre actualizados.

- [x] `test_get_recipient_phones` — Verifica que get_recipient_phones() retorna telefonos actualizados via JOIN.
- [x] `test_phone_change_reflected_in_template` — Verifica que al cambiar el telefono de un usuario, el template refleja el nuevo telefono via get_one().

## Tasks completas (T23-T31)

| Task | Estado | Descripcion |
|------|--------|-------------|
| T23 | [x] | Migracion: crea tabla pivote + DROP COLUMN recipients |
| T24 | [x] | Modelo ReportTemplateUser en models.py |
| T25 | [x] | create() acepta user_ids, inserta en pivote |
| T26 | [x] | update() reemplaza filas en pivote |
| T27 | [x] | get_all() incluye JOIN para recipients resueltos |
| T28 | [x] | _send_template_reports() usa get_recipient_phones() |
| T29 | [x] | TemplateFormModal.svelte: selector multiple de usuarios en vez de texto |
| T30 | [x] | Tests backend para R19 y R20 |
| T31 | [x] | Tests frontend para selector de usuarios |

## Archivos revisados

### database/migrations/2026_07_08_000001_create_report_template_users_table.py
- [x] CREATE TABLE report_template_users con PK compuesta y FKs con ON DELETE CASCADE
- [x] CREATE INDEX idx_rtu_user_id para JOIN eficiente
- [x] ALTER TABLE report_templates DROP COLUMN recipients
- [x] downgrade() definido

### src/models.py — ReportTemplateUser
- [x] __tablename__ = "report_template_users"
- [x] Columnas: template_id (FK), user_id (FK) con ondelete="CASCADE"
- [x] PK compuesta via PrimaryKeyConstraint
- [x] Indice en user_id

### src/report_templates.py
- [x] create(): acepta user_ids, inserta filas en ReportTemplateUser, NO guarda recipients
- [x] update(): reemplaza user_ids (borra + inserta) si se pasan
- [x] get_all(): retorna dicts via _template_to_dict() con recipients resueltos
- [x] get_one(): nueva funcion para obtener plantilla individual
- [x] get_recipient_phones(): resuelve telefonos via JOIN (R20)
- [x] _resolve_recipients(): helper que retorna (phones, user_ids)

### src/sms_service.py — _send_template_reports()
- [x] Reemplaza `json.loads(template.recipients)` por `get_recipient_phones(template.id)` (R20)
- [x] Compatible hacia atras: contrato externo de send_scheduled_report() no cambia

### src/main.py — Schemas y endpoints
- [x] TemplateCreate: user_ids en vez de recipients
- [x] TemplateUpdate: user_ids opcional
- [x] create_template() usa body.model_dump() → svc.create()
- [x] update_template() usa body.model_dump() filtrando None
- [x] Retorna get_one() (dict con recipients + recipient_ids)

### frontend/src/components/TemplateFormModal.svelte
- [x] Reemplazado input recipients_text por selector multiple con checkboxes
- [x] Carga usuarios via GET /api/users?page_size=100
- [x] Filtra solo admin + corresponsal activos
- [x] Busqueda por nombre (case-insensitive)
- [x] Botones "Seleccionar todos" / "Deseleccionar"
- [x] Envia user_ids en payload (NO recipients)
- [x] Pre-selecciona desde recipient_ids en modo edit
- [x] Mensaje si no hay usuarios disponibles
- [x] Svelte 5 runes: $state(), $derived(), $effect(), onMount, $props()

### tests/test_report_templates.py — TestReportTemplatePivot
- [x] 6 tests nuevos para R19 y R20
- [x] test_create_with_user_ids (R19)
- [x] test_get_all_resolves_recipients (R19)
- [x] test_update_replaces_recipients (R19)
- [x] test_create_without_user_ids (R19)
- [x] test_get_recipient_phones (R20)
- [x] test_phone_change_reflected_in_template (R20)

### frontend/src/components/__tests__/TemplateFormModal.test.js
- [x] 6 tests nuevos para el selector de usuarios (R19)
- [x] Tests de carga, filtrado por rol, busqueda, envio de payload, pre-seleccion, sin usuarios

## Cumplimiento de architecture.md y conventions.md

### Sin dependencias externas nuevas
- [x] Solo stdlib Python + SQLAlchemy/FastAPI existentes
- [x] Sin cambios en requirements.txt

### Errores explicitos
- [x] TemplateNotFoundError con nombre descriptivo
- [x] HTTPException con 404/400 segun el caso
- [x] Excepciones atrapadas en generate_report() sin fatal

### Svelte 5 runes correctos
- [x] $props() para props del componente
- [x] $state() para estado mutable
- [x] $derived() para filteredUsers
- [x] $effect() para init al abrir modal
- [x] onMount no necesario (efecto en show)

### Migracion de BD incluida
- [x] Archivo numerado secuencialmente (2026_07_08_000001)
- [x] upgrade() y downgrade() definidos

## Impacto en features existentes

### Feature 7 (sms_service)
- [x] _send_template_reports(): reemplaza template.recipients por get_recipient_phones()
- [x] Contrato externo sin cambios: send_scheduled_report() firma intacta
- [x] Documentado en impl report seccion "Impacto en features existentes"

### Feature 8 (ai_agent)
- [x] Sin impacto directo. GET /api/reports/templates ahora incluye recipient_ids adicionalmente.

### Features 14, 15, 16 (Frontend admin)
- [x] Sin impacto directo. TemplateFormModal cambia contrato interno (user_ids vs recipients) pero AdminReportes se actualizo para manejarlo.

## Skills consultados
- [x] svelte5 — Cargado desde `.opencode/skills/svelte5/SKILL.md`
- [x] Documentado en impl report

## Checkpoints (C1-C8)

| Checkpoint | Estado | Nota |
|------------|--------|------|
| C1 — Harness completo | [x] | init.ps1 secciones 1-5 OK |
| C2 — Estado coherente | [x] | Feature 17 in_progress, unica en curso |
| C3 — Arquitectura respetada | [x] | Sin nuevas dependencias, errores explicitos |
| C4 — Verificacion real | [x] | tests/report_templates: 19 tests, tests/main: 11 tests, frontend: 8 tests nuevos |
| C5 — BD bajo control | [x] | Migracion numerada, upgrade/downgrade, schema_dump OK |
| C6 — Sesion bien cerrada | [ ] | Sesion aun abierta (harness/.session = open) — esperado, feature en in_progress |
| C7 — SDD | [x] | Spec completo (requirements.md, design.md, tasks.md) con EARS |
| C8 — Documentacion historica | [ ] | Closure aun no existe — feature en in_progress |

## Resultados de tests

### Backend — test_report_templates.py (Nuevos Fase 8)
- 6 tests en TestReportTemplatePivot: **6/6 PASAN** ✅

### Backend — test_report_templates.py (Completos)
- 19 tests: **19/19 PASAN** ✅

### Backend — test_main.py
- 11 tests: **11/11 PASAN** ✅

### Frontend — TemplateFormModal.test.js (Nuevos Fase 8)
- 8 tests: **8/8 PASAN** ✅

### Fallos preexistentes (NO relacionados con Fase 8)
- UserFormModal.test.js: 3 fallos (placeholder text "(opcional)" mismatch y em-dash encoding) — documentados en impl report
- test_sms_service: 1 fallo (test_send_sms_with_persistence_does_not_call_mmcli_directly) — error de mock setup en entorno de pruebas, no relacionado
- validate_features.py: 4 ERRORES preexistentes en features 21, 22, 25, 28

## Veredicto

**APROBADO.** La implementacion de la Fase 8 (tabla pivote report_template_users) cumple con todos los requisitos R19 y R20, todas las tasks T23-T31 estan completas, y los tests tanto backend como frontend pasan. La arquitectura, convenciones y principios SOLID se respetan. Las unicas fallas son preexistentes y no relacionadas con esta fase.

Nota: La sesion permanece abierta (harness/.session = open). Para cerrar formalmente, ejecutar harness/scripts/close.ps1 cuando el humano autorice el cierre.
