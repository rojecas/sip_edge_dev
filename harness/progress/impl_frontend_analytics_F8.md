# Feature 17 — Frontend Analytics: Fase 8 Implementation Report

> **Estado:** Implementación completa (T23-T31). Listo para revisión.
> **Fecha:** 2026-07-08

---

## Resumen

Fase 8 normaliza los destinatarios de plantillas de reportes usando una tabla pivote
`report_template_users` en vez de almacenar telefonos como JSON en `report_templates.recipients`.

**Problema resuelto:** Los telefonos se desincronizaban si un usuario cambiaba su numero.
**Solución:** Tabla pivote con FKs a `report_templates` y `users`. Los telefonos se resuelven
via JOIN al enviar reportes, garantizando que siempre esten actualizados.

---

## Archivos creados

| # | Archivo | Descripción |
|---|---------|------------|
| 1 | `database/migrations/2026_07_08_000001_create_report_template_users_table.py` | Migración: crea tabla pivote + DROP COLUMN recipients |

## Archivos modificados

| # | Archivo | Cambio |
|---|---------|--------|
| 1 | `src/models.py` | Agregado `ReportTemplateUser(Base)` con PK compuesta (template_id, user_id), FKs con ON DELETE CASCADE, índice en user_id. Eliminada columna `recipients` de `ReportTemplate`. Agregado import `PrimaryKeyConstraint`. |
| 2 | `src/report_templates.py` | `create()`: acepta `user_ids`, inserta filas en pivote, no guarda `recipients`. `update()`: reemplaza filas en pivote si se pasan `user_ids`. `get_all()`: retorna `list[dict]` con destinatarios resueltos via JOIN. Agregados `get_one()`, `get_recipient_phones()`, `_resolve_recipients()`, `_template_to_dict()`. |
| 3 | `src/sms_service.py` | `_send_template_reports()`: reemplaza `json.loads(template.recipients)` por `get_recipient_phones(template.id)` — resuelve telefonos via JOIN a tabla pivote + users. |
| 4 | `src/main.py` | `TemplateCreate`: `recipients` → `user_ids`. `TemplateUpdate`: `recipients` → `user_ids`. Endpoints `list_templates`, `create_template`, `update_template` adaptados a las nuevas firmas del servicio (dict con `recipients` + `recipient_ids` resueltos). |
| 5 | `frontend/src/components/TemplateFormModal.svelte` | Reemplazado input `recipients_text` por selector multiple de usuarios con checkboxes. Carga usuarios via `GET /api/users?page_size=100`, filtra admin + corresponsal activos, muestra `full_name` + `phone`, incluye búsqueda por nombre, botones "Seleccionar todos"/"Deseleccionar". Envia `user_ids` en el payload (NO `recipients`). |
| 6 | `tests/test_report_templates.py` | Actualizados tests existentes para usar `user_ids` en vez de `recipients` y acceso dict (`t["name"]`) en `get_all()`. Agregada clase `TestReportTemplatePivot` con 6 tests nuevos (R19, R20). |
| 7 | `frontend/src/components/__tests__/TemplateFormModal.test.js` | Agregados 6 tests en `selector de usuarios (R19)`: carga de usuarios, filtro de roles, filtro por búsqueda, envío de `user_ids`, mensaje sin usuarios disponibles. Actualizados tests existentes para compatibilidad con nuevo API mock. |

---

## Impacto en features existentes

### Feature 7 (sms_service)
- **Archivo:** `src/sms_service.py`, método `_send_template_reports()`
- **Cambio:** Ya no lee `template.recipients` (JSON). Ahora usa `get_recipient_phones(template.id)` que resuelve telefonos via JOIN a `report_template_users` + `users`.
- **Compatibilidad:** Totalmente compatible. El contrato externo de `send_scheduled_report()` no cambia.

### Feature 8 (ai_agent)
- Sin impacto directo. El endpoint `GET /api/reports/templates` ahora retorna `recipient_ids` adicionalmente, pero el response sigue incluyendo `recipients` (telefonos resueltos).

### Features 14, 15, 16 (Frontend admin)
- Sin impacto. El `AdminReportes.svelte` consume el mismo endpoint `GET /api/reports/templates` cuyo response incluye ahora `recipient_ids` adicionalmente. `TemplateFormModal.svelte` cambió su contrato interno con `AdminReportes.svelte`: envía `user_ids` en vez de `recipients`, y espera `recipient_ids` para pre-seleccionar en modo edición.

---

## Trazabilidad R<n> → Tests

| R# | Descripción | Test(s) |
|----|-------------|---------|
| R19 | Almacenar destinatarios como user_id en tabla pivote | `test_create_with_user_ids`, `test_get_all_resolves_recipients`, `test_update_replaces_recipients`, `test_create_without_user_ids` (backend); `carga usuarios via GET /api/users al abrir`, `muestra solo admin y corresponsal activos`, `filtra usuarios por nombre con la busqueda`, `envia user_ids en el payload al guardar`, `modo edit pre-selecciona usuarios desde recipient_ids`, `muestra mensaje si no hay usuarios admin/corresponsal activos` (frontend) |
| R20 | Resolver telefonos via JOIN al enviar reportes | `test_get_recipient_phones`, `test_phone_change_reflected_in_template` (backend) |

---

## Resultados de tests

### Backend (Python — unittest)
- **Tests ejecutados:** 19 (test_report_templates.py)
- **Pasaron:** 19 ✅
- **Fallaron:** 0

### Backend (test_main.py — verificación de no rotura)
- **Tests ejecutados:** 11
- **Pasaron:** 11 ✅

### Frontend (Svelte — vitest)
- **Nuevos tests (Fase 8):** 6 (TemplateFormModal.test.js)
- **Tests totales TemplateFormModal:** 9
- **Pasaron (TemplateFormModal):** 9 ✅
- **Fallos preexistentes (no relacionados):** 3 (UserFormModal.test.js — placeholder text y em-dash)

---

## Desviaciones del spec

Ninguna. Todas las tasks T23-T31 fueron implementadas según lo especificado en `design.md` y `tasks.md`.

### Decisiones de implementación

1. **`get_all()` retorna dicts, no ORM objects.** Era necesario para incluir `recipients` + `recipient_ids` resueltos. Los métodos `create()`/`update()` siguen retornando ORM objects. Se agregaron `get_one()` y `get_recipient_phones()` para cubrir los casos de uso restantes.

2. **`ReportTemplate.recipients` eliminado del modelo ORM.** La migración incluye `DROP COLUMN recipients` para producción. En dev, `Base.metadata.create_all` no elimina la columna existente (solo crea tablas), pero el código ya no la referencia — es inofensiva.

3. **Backward compatibility en API.** Si el frontend viejo envía `recipients` en el body, Pydantic lo ignora (extra fields se descartan por defecto). El comportamiento es silencioso y no produce errores.

4. **FKs con ON DELETE CASCADE.** Al eliminar una plantilla o usuario, las filas correspondientes en `report_template_users` se eliminan automáticamente. El método `delete()` del servicio no necesita cambios.

---

## Skills consultados

- **svelte5** — Cargado desde `.opencode/skills/svelte5/SKILL.md`. Aplicado para: `$state`, `$effect`, `$derived`, `onMount`, patrones de props con `$props()`.
