# Review — feature 17 (frontend_analytics)

**Veredicto:** CHANGES_REQUESTED

## Trazabilidad requirements <-> tests

| R# | Estado | Test(s) | Notas |
|----|--------|---------|-------|
| R1 | [x] | AdminReportes.test.js: "llama GET /api/reports/templates al montar", "renderiza tabla con plantillas" | |
| R2 | [x] | AdminReportes.test.js: "muestra mensaje de error si GET falla", "muestra boton Reintentar en el error" | |
| R3 | [x] | AdminReportes.test.js: "muestra mensaje vacio si no hay plantillas" | |
| R4 | [x] | TemplateFormModal.test.js: "modo edit pre-puebla campos desde plantilla". AdminReportes.test.js: "abre modal al pulsar '+ Nueva Plantilla'" | Cobertura débil (no verifica cada campo específico), pero aceptable |
| R5 | [x] | TemplateFormModal.test.js: "muestra error si nombre esta vacio al guardar", "llama onSave si el nombre esta completo" | |
| R6 | [ ] | **Sin test** — La implementación (handleDelete, confirmDelete en AdminReportes.svelte) existe pero no hay test que verifique el flujo de eliminación con confirmación | **GAP** |
| R7 | [x] | AdminAnomalias.test.js + test_main.py (3 tests de paginación, estructura de items, defaults) | |
| R8 | [x] | AdminAnomalias.test.js (4 tests de paginación UI) + test_main.py (page_2, last_page, page_size_max) | |
| R9 | [x] | AdminAgente.test.js: "muestra mensaje de bienvenida al montar" | |
| R10 | [x] | AdminAgente.test.js: "envía consulta y muestra respuesta" | |
| R11 | [x] | AdminAgente.test.js: "muestra 'Pensando...' mientras el agente procesa", "deshabilita input y boton durante carga" | |
| R12 | [x] | AdminAgente.test.js: "muestra mensaje de error si POST falla", "muestra boton Reintentar al fallar" | |
| R13 | [x] | AdminAnomalias.test.js: "muestra panel al pulsar 'Detectar Ahora'" | |
| R14 | [x] | test_main.py: test_detect_anomalies_custom_params, test_detect_anomalies_with_tipo_cosecha | |
| R15 | [ ] | **Sin test** — El estado detectEmpty existe en AdminAnomalias.svelte (líneas 96-98, 188-193), pero no hay test que verifique el mensaje "No se detectaron anomalías" | **GAP** |
| R16 | [x] | Cubierto por interceptor 401 existente en api.js (probado en F14). Las nuevas rutas usan el mismo wrapping {#if .isAdmin} | Aceptable |
| R17 | [x] | Verificación manual (T22). Los links existen en AdminLayout.svelte (líneas 21-23) | Sin test automatizado, pero T22 es verificación visual aceptable |
| R18 | [x] | Verificación manual (T22). Las cards existen en AdminDashboard.svelte (líneas 33-55) | Sin test automatizado, pero T22 es verificación visual aceptable |

**Resumen:** R6 y R15 no tienen cobertura de test. Violación de la regla dura "Cada R<n> debe tener al menos un test concreto".

## Tasks completas

| Task | Estado | Notas |
|------|--------|-------|
| T1-T4 (Backend paginación) | [x] | Implementado en src/main.py líneas 678-734 + tests en test_main.py |
| T5 (Constantes) | [x] | constants.js líneas 29-33 |
| T6 (Sidebar links) | [x] | AdminLayout.svelte líneas 21-23 |
| T7 (Dashboard cards) | [x] | AdminDashboard.svelte líneas 33-55 |
| T8 (App.svelte imports) | [x] | App.svelte líneas 22-24, 71-76 |
| T9 (AdminReportes.svelte) | [x] | 248 líneas, cubre loading/error/empty/tabla + modal |
| T10 (TemplateFormModal.svelte) | [x] | 367 líneas, cubre todos los campos del spec |
| T11 (Guardar/Eliminar) | [x] | handleSave y handleDelete implementados |
| T12 (AdminAnomalias.svelte) | [x] | 360 líneas, tabla paginada completa |
| T13 (Detectar Ahora) | [x] | Panel de parámetros + resultados en AdminAnomalias |
| T14 (AdminAgente.svelte) | [x] | 253 líneas, chat completo con loading/error/retry |
| T15 (AdminReportes test) | [x] | 8 tests |
| T16 (TemplateFormModal test) | [x] | 3 tests |
| T17 (AdminAnomalias test) | [x] | 10 tests |
| T18 (AdminAgente test) | [x] | 3 tests (envío) |
| T19 (AdminAgente loading test) | [x] | 2 tests (loading + disabled) |
| T20 (Backend detect test) | [x] | 3 tests en test_main.py |
| T21 (init.ps1) | [x] | Secciones 1-5 [OK] |
| T22 (Verificación visual) | [x] | Manual |

Todas las tasks están [x].

## Checkpoints (C1-C8)

- C1: [x] — Harness completo, init.ps1 secciones 1-5 OK
- C2: [ ] — Hay features con in_progress (feature 17), es correcto. Faltan tests para R6 y R15 → no puede pasar a done
- C3: [x] — Código respeta arquitectura, sin dependencias externas no declaradas
- C4: [ ] — Tests cubren la mayoría de módulos. Faltan tests para R6, R15
- C5: [x] — No toca BD
- C6: [ ] — Sesión actual no cerrada (init.ps1 mostró WARN en 1.5)
- C7: [ ] — Faltan tests para R6 y R15 (incumple "cada R<n> cubierto por al menos un test")
- C8: [ ] — Feature 17 está in_progress, sin closure aún

## GitHub sync

- [ ] Feature 17 no tiene campo github_issue en feature_list.json, pero harness/github.json tiene enabled: true. Falta crear el issue.

## Skills consultados

- [ ] **Skills documentation missing** — El stack usa Svelte 5. Existe el skill svelte5 en .opencode/skills/svelte5/SKILL.md. El implementer NO documentó haberlo cargado. El reporte de implementación no menciona skills consultados. Esto viola la regla: "Si hay skill para el stack, el implementer DEBE haberlo cargado. Rechaza si falta la documentacion."

## Impacto en features existentes

- [x] Sección documentada en impl_frontend_analytics.md (líneas 34-45)
- [x] Feature 8 (ai_agent): cambio a GET /api/anomalies/history documentado como rompimiento de compatibilidad
- [x] Features 14, 15, 16: modificaciones compatibles hacia atrás documentadas

## Cumplimiento de architecture.md

- [x] Capas respetadas: frontend componentes Svelte 5 independientes, backend con endpoints FastAPI
- [x] Sin dependencias externas no declaradas
- [x] Errores explícitos (ApiError, excepciones con mensajes)
- [x] Atomicidad en disco no aplica (sin writes directos a disco)

## Cumplimiento de conventions.md (frontend)

- [x] Svelte 5 runes correctamente usados (, , , )
- [x] Nombres PascalCase para componentes, snake_case para variables internas
- [x] Imports ordenados, strings con comillas dobles
- [x] Tests sin mocks de sistema de archivos (usan vitest mocks de api)

## Cumplimiento de specs.md

- [x] Requirements en EARS
- [x] Tasks referencian R<n>
- [ ] R6 y R15 no verificables por test actual

## Release

- [ ] La feature no está lista para release-manager hasta que se corrijan los gaps

## Cambios requeridos

1. **Añadir test para R6** — Agregar test en AdminReportes.test.js que verifique el flujo de eliminación: click botón 🗑️ → se muestra ConfirmModal → confirmar → se llama pi.del(REPORTS_TEMPLATES_BY_ID + id) → se recarga tabla.

2. **Añadir test para R15** — Agregar test en AdminAnomalias.test.js que verifique que al ejecutar detección y obtener resultados vacíos, se muestra "No se detectaron anomalías con los parámetros seleccionados."

3. **Documentar skills consultados** — Agregar sección en impl_frontend_analytics.md (o archivo separado) que documente la carga del skill svelte5 y cualquier otro skill relevante usado durante la implementación.

4. **Crear GitHub issue** — Agregar campo github_issue a feature 17 en eature_list.json con la URL del issue creado.
