# Closure — Feature 15: Frontend Admin — Configuración y Backup (14b)

> **Feature:** frontend_admin_operations
> **ID:** 15
> **Tipo:** feature
> **Estado:** done
> **Fecha de cierre:** 2026-06-19
> **Spec:** harness/specs/15_frontend_admin_operations/

---

## Resumen

Feature frontend-only que verifica el panel de configuración del sistema
(AdminConfig.svelte) y corrige un bug crítico de field name mismatch en el
panel de backups (AdminBackup.svelte). El código fuente ya existía del
desarrollo de feature 14.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| frontend/src/components/AdminBackup.svelte | Corregidos 7 field names: archivo→filename, tamano→file_size, checksum_local→local_checksum, copia_usb→usb_copied, checksum_usb→usb_checksum, error→error_message, fecha→created_at |
| src/static/* | Copiado nuevo build de frontend (npm run build) |
| harness/specs/15_frontend_admin_operations/tasks.md | Marcadas todas las tasks [x] |
| harness/feature_list.json | Status actualizado a in_progress, github_issue añadido |

## Decisiones técnicas

1. **Field name mapping directo:** Se cambian los nombres en el template en vez
   de crear una capa de adaptación, porque el backend es la única fuente de
   verdad y sus nombres están en inglés.
2. **AdminConfig.svelte no se modificó:** Ya funcionaba correctamente.
3. **Sin cambios en backend:** Todos los endpoints ya existen.

## Verificación

| Nivel | Resultado |
|-------|-----------|
| N1 — Tests unitarios backend | 443 tests OK |
| N2 — Build frontend | npm run build exitoso (150 modules) |
| N3 — init.ps1 | Todos los bloques [OK] |
| N4 — EdgeBox | No aplica (frontend-only) |

## Trazabilidad R<n> → verificación

Ver harness/progress/impl_frontend_admin_operations.md sección "Trazabilidad".

## GitHub Issue

https://github.com/rojecas/sip_edge/issues/17

## Aprobación

Reviewer: APPROVED (harness/progress/review_frontend_admin_operations.md)

## Tests frontend (agregados en Fase 4)

| Componente | Tests | Framework |
|------------|-------|-----------|
| AdminConfig.svelte | 21 tests (carga, guardado, tests de puerto, timeouts, estados) | Vitest + @testing-library/svelte + jsdom |
| AdminBackup.svelte | 12 tests (carga, tabla con field names corregidos, ejecutar backup, disable 30s, error handling, refresh) | Vitest + @testing-library/svelte + jsdom |

**Resultado:** 33/33 tests passed, 3.76s.

### Archivos nuevos
| Archivo | Propósito |
|---------|-----------|
| frontend/vitest.config.js | Configuración de Vitest (jsdom, setup) |
| frontend/src/setupTest.js | Setup de testing-library/jest-dom |
| frontend/src/components/__tests__/AdminConfig.test.js | 21 tests para AdminConfig |
| frontend/src/components/__tests__/AdminBackup.test.js | 12 tests para AdminBackup |
| frontend/package.json | Script "test": "vitest run" añadido |
