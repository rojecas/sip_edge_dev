# Feature 17 — Frontend Analytics: Tasks

> Checklist ejecutable. Cada task referencia los `R<n>` que cubre.

---

## Fase 1 — Backend: agregar paginación a anomalías

- [x] T1 — Modificar `GET /api/anomalies/history` en `src/main.py` para aceptar `page` (default 1) y `page_size` (default 20, max 100) y retornar `PaginatedResponse[AnomalyLogResponse]`. Cubre: R7, R8.
- [x] T2 — Añadir schema `AnomalyLogResponse` (Pydantic `BaseModel`) con los campos del log y `from_attributes = True` junto al endpoint. Cubre: R7.
- [x] T3 — Añadir test `test_anomaly_history_pagination` en `tests/test_main.py` que verifique response paginado con page/page_size/total/total_pages. Cubre: R7, R8.
- [x] T4 — Añadir test `test_anomaly_history_default_params` en `tests/test_main.py` que verifique defaults (page=1, page_size=20). Cubre: R7.

## Fase 2 — Constantes y routing

- [x] T5 — Agregar constantes de endpoints en `frontend/src/lib/constants.js`:
  - `REPORTS_TEMPLATES: "/api/reports/templates"`
  - `REPORTS_TEMPLATES_BY_ID: "/api/reports/templates/"`
  - `ANOMALIES_HISTORY: "/api/anomalies/history"`
  - `ANOMALIES_DETECT: "/api/anomalies"`
  - `AGENT_QUERY: "/api/agent/query"`
  Subtask: importar `ENDPOINTS` en cada nuevo componente. Cubre: R1, R7, R10, R13.
- [x] T6 — Agregar en `frontend/src/components/AdminLayout.svelte` los links al sidebar:
  - `/admin/reportes` → "Reportes" con icono 📋
  - `/admin/anomalias` → "Anomalías" con icono ⚠️
  - `/admin/agente` → "Agente IA" con icono 🤖
  Cubre: R17.
- [x] T7 — Agregar en `frontend/src/components/AdminDashboard.svelte` las cards de acceso rápido:
  - Reportes: ruta `/admin/reportes`, descripción "Plantillas de reportes programados."
  - Anomalías: ruta `/admin/anomalias`, descripción "Historial de anomalías detectadas."
  - Agente IA: ruta `/admin/agente`, descripción "Consola de consultas al agente inteligente."
  Cubre: R18.
- [x] T8 — En `frontend/src/App.svelte`:
  - Importar los 3 nuevos componentes
  - Agregar condiciones de ruta para `/admin/reportes`, `/admin/anomalias`, `/admin/agente`
  Cubre: R1, R7, R9, R16.

## Fase 3 — Componente AdminReportes

- [x] T9 — Crear `frontend/src/components/AdminReportes.svelte`:
  - `onMount` carga plantillas via `api.get(ENDPOINTS.REPORTS_TEMPLATES)`
  - Tabla con columnas: ID, Nombre, Schedule, Métricas, Activo, Acciones (Editar/Eliminar)
  - Estados: loading, error con Reintentar, empty ("No hay plantillas de reportes")
  - Botón "+ Nueva Plantilla" que abre `TemplateFormModal` en modo create
  Cubre: R1, R2, R3.
- [x] T10 — Crear `frontend/src/components/TemplateFormModal.svelte`:
  - Props: `show`, `mode`, `plantilla`, `error`, `onClose`, `onSave`
  - Campos: nombre (input text), schedule (multiselect de horas o checkboxes), recipients (input text para teléfonos separados por coma), metrics (checkboxes con lista de métricas disponibles: count, avg, min_max, breakdown_by_hacienda, breakdown_by_operator, composition, anomaly_count, trend), is_active (checkbox)
  - Validación: nombre requerido
  - Botones: Cancelar / Guardar
  - Sigue el patrón de `UserFormModal.svelte` (overlay, container, header, body, actions)
  Cubre: R4, R5.
- [x] T11 — Implementar guardado y eliminación en `AdminReportes.svelte`:
  - `handleSave(payload)`: si mode="create" → `api.post(ENDPOINTS.REPORTS_TEMPLATES, payload)`, si mode="edit" → `api.put(ENDPOINTS.REPORTS_TEMPLATES_BY_ID + id, payload)`
  - `handleDelete(plantilla)`: mostrar `ConfirmModal`, si confirma → `api.del(ENDPOINTS.REPORTS_TEMPLATES_BY_ID + id)`
  - Tras cada operación exitosa: recargar tabla, mostrar mensaje de éxito temporizado
  - En error: mostrar mensaje de error del servidor en el modal o en un banner
  Cubre: R5, R6.

## Fase 4 — Componente AdminAnomalias

- [x] T12 — Crear `frontend/src/components/AdminAnomalias.svelte`:
  - `onMount` carga historial via `api.get(ENDPOINTS.ANOMALIES_HISTORY + queryParams)`
  - Tabla con columnas: ID, Capa, Z-Score, Valor Métrica, Umbral, Reporte LLM, SMS Enviado, Fecha
  - Paginación: controles Anterior/Siguiente, selector page size (10/20/50/100), "Página X de Y (Z registros)"
  - Estados: loading, error con Reintentar, empty ("No hay anomalías registradas")
  - Sigue el patrón de `AdminBackup.svelte` para paginación y manejo de estados
  Cubre: R7, R8.
- [x] T13 — Agregar botón "Detectar Ahora" con panel de parámetros configurables en `AdminAnomalias.svelte`:
  - Panel colapsable/visible con: `window_size` (input number, default 120), `z_threshold` (input number step 0.1, default 3.0), `tipo_cosecha` (select opcional con opciones de HARVEST_TYPES + "Todas")
  - Botón "Ejecutar Detección" → `api.get(ENDPOINTS.ANOMALIES_DETECT + buildQuery({window, threshold, tipo_cosecha}))`
  - Resultados en tabla debajo del panel (mismas columnas que historial pero sin LLM Report/SMS/Fecha)
  - Loading state mientras se ejecuta, "No se detectaron anomalías" si resultados vacíos
  Cubre: R13, R14, R15.
- [x] T14 — Crear `frontend/src/components/AdminAgente.svelte`:
  - Área de chat: contenedor scrollable con mensajes alternados (user alineado derecha, agente alineado izquierda)
  - Campo de texto + botón "Enviar" al pie
  - `onMount`: inicializar con mensaje de bienvenida del sistema
  - `handleSend`: agregar mensaje del usuario al array, llamar `api.post(ENDPOINTS.AGENT_QUERY, {query})`, agregar respuesta al array
  - Loading: mostrar "Pensando..." con spinner, deshabilitar input y botón
  - Error en consulta: mostrar mensaje de error en el chat + botón "Reintentar" junto al último mensaje fallido
  Cubre: R9, R10, R11, R12.

## Fase 6 — Tests

- [x] T15 — Añadir test `test_admin_reportes_loads_templates` (frontend) en `frontend/src/components/__tests__/AdminReportes.test.js` que verifique carga de plantillas. Cubre: R1.
- [x] T16 — Añadir test `test_template_form_modal_validation` (frontend) que verifique validación de nombre vacío. Cubre: R5.
- [x] T17 — Añadir test `test_admin_anomalias_pagination` (frontend) que verifique carga de página y cambio de page size. Cubre: R7, R8.
- [x] T18 — Añadir test `test_admin_agente_send_query` (frontend) que verifique envío de consulta y visualización de respuesta. Cubre: R10.
- [x] T19 — Añadir test `test_admin_agente_loading_state` (frontend) que verifique deshabilitado del input durante carga. Cubre: R11.
- [x] T20 — Añadir test `test_anomaly_detect_on_demand` (backend) en `tests/test_main.py` que verifique GET /api/anomalies con parámetros custom. Cubre: R14.

## Fase 7 — Verificación final

- [x] T21 — Verificar que `./init.ps1` termina sin errores. Cubre: R1-R18.
- [x] T22 — Verificar navegación manual: sidebar links funcionales, cards del dashboard redirigen correctamente, breadcrumbs o títulos de página son descriptivos. Cubre: R17, R18.

---

## Trazabilidad

| R# | Tasks | Tests |
|----|-------|-------|
| R1 | T5, T8, T9 | T15 |
| R2 | T9 | — |
| R3 | T9 | — |
| R4 | T10 | — |
| R5 | T10, T11 | T16 |
| R6 | T11 | — |
| R7 | T1, T2, T3, T4, T5, T12 | T3, T4, T17 |
| R8 | T1, T12 | T3, T17 |
| R9 | T8, T14 | — |
| R10 | T5, T14 | T18 |
| R11 | T14 | T19 |
| R12 | T14 | — |
| R13 | T5, T13 | — |
| R14 | T13 | T20 |
| R15 | T13 | — |
| R16 | T8 | — |
| R17 | T6 | T22 |
| R18 | T7 | T22 |

## Fase 8 - Tabla pivote report_template_users (R19, R20)
- [x] T23 - Crear migracion database/migrations/2026_07_08_000001_create_report_template_users_table.py: CREATE TABLE report_template_users (template_id FK, user_id FK, PK compuesta), ALTER TABLE report_templates DROP COLUMN recipients. Cubre: R19.
- [x] T24 - Agregar modelo ReportTemplateUser en src/models.py con __tablename__ = ""report_template_users"", columnas template_id y user_id, FK a ReportTemplate y User. Cubre: R19.
- [x] T25 - Actualizar ReportTemplateService.create() en src/report_templates.py: aceptar user_ids en data, insertar filas en report_template_users, ya NO guardar JSON en recipients. Cubre: R19.
- [x] T26 - Actualizar ReportTemplateService.update() en src/report_templates.py: reemplazar filas en report_template_users (borrar existentes + insertar nuevas). Cubre: R19.
- [x] T27 - Actualizar ReportTemplateService.get_all() en src/report_templates.py: incluir JOIN a report_template_users + users para retornar 
ecipients (telefonos) y 
ecipient_ids (user_ids). Cubre: R19, R20.
- [x] T28 - Actualizar _send_template_reports() en src/sms_service.py: leer telefonos via JOIN desde pivote + users, no desde template.recipients. Cubre: R20.
- [x] T29 - Actualizar TemplateFormModal.svelte: reemplazar input recipients_text por selector multiple de usuarios (checkboxes). Cargar usuarios via GET /api/users, filtrar solo admin + corresponsal activos. Enviar user_ids en payload. Cubre: R19.
- [x] T30 - Agregar test en 	ests/test_report_templates.py (o 	est_main.py) que verifique creacion con user_ids, y que recipients se resuelven desde users. Cubre: R19, R20.
- [x] T31 - Agregar test frontend en TemplateFormModal.test.js que verifique que el selector de usuarios carga, filtra y envia user_ids correctamente. Cubre: R19.
## Trazabilidad (actualizada)

| R# | Tasks | Tests |
|----|-------|-------|
| R1 | T5, T8, T9 | T15 |
| R2 | T9 | - |
| R3 | T9 | - |
| R4 | T10 | - |
| R5 | T10, T11 | T16 |
| R6 | T11 | - |
| R7 | T1, T2, T3, T4, T5, T12 | T3, T4, T17 |
| R8 | T1, T12 | T3, T17 |
| R9 | T8, T14 | - |
| R10 | T5, T14 | T18 |
| R11 | T14 | T19 |
| R12 | T14 | - |
| R13 | T5, T13 | - |
| R14 | T13 | T20 |
| R15 | T13 | - |
| R16 | T8 | - |
| R17 | T6 | T22 |
| R18 | T7 | T22 |
| R19 | T23, T24, T25, T26, T27, T29 | T30, T31 |
| R20 | T27, T28 | T30 |
