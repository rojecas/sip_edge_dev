# Feature 17 - Frontend Analytics: Design

## Resumen

Feature que agrega tres nuevas vistas administrativas: Reportes Programados (CRUD de plantillas),
Historial de Anomalias (tabla paginada) y Consola del Agente IA (chat).
Incluye normalizacion de destinatarios via tabla pivote report_template_users.

---

## Archivos a crear

| Archivo | Proposito |
|---------|-----------|
| frontend/src/components/AdminReportes.svelte | Vista CRUD de plantillas de reportes |
| frontend/src/components/TemplateFormModal.svelte | Modal de creacion/edicion de plantilla |
| frontend/src/components/AdminAnomalias.svelte | Vista de historial de anomalias paginado |
| frontend/src/components/AdminAgente.svelte | Interfaz tipo chat para consultas al agente |

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| frontend/src/App.svelte | Agregar imports y condicionales de ruta |
| frontend/src/components/AdminLayout.svelte | Agregar links al sidebar |
| frontend/src/components/AdminDashboard.svelte | Agregar cards de acceso rapido |
| frontend/src/lib/constants.js | Agregar constantes de endpoints |
| src/main.py | Refactorizar GET /api/anomalies/history con paginacion |
| src/models.py | Agregar modelo ReportTemplateUser para tabla pivote |
| src/report_templates.py | Reemplazar JSON recipients por CRUD en tabla pivote |
| src/sms_service.py | Resolver telefonos via JOIN desde tabla pivote |

---

## Firmas nuevas (frontend)

### Componentes Svelte

AdminReportes.svelte
  Props: ninguna (self-contained)
  State interno: plantillas[], loading, loadError, emptyMsg, formShow, formMode, formPlantilla

TemplateFormModal.svelte
  Props: show, mode, plantilla, error, onClose, onSave
  State interno: form { name, schedule, selectedUserIds[], metrics, is_active }
  + carga GET /api/users para poblar selector de destinatarios

AdminAnomalias.svelte
  Props: ninguna (self-contained)
  State interno: anomalias[], loading, loadError, currentPage, totalPages, pageSize

AdminAgente.svelte
  Props: ninguna (self-contained)
  State interno: messages[{role, content}], inputText, loading, error

### Nuevas constantes en constants.js
REPORTS_TEMPLATES: /api/reports/templates
REPORTS_TEMPLATES_BY_ID: /api/reports/templates/
ANOMALIES_HISTORY: /api/anomalies/history
ANOMALIES_DETECT: /api/anomalies
AGENT_QUERY: /api/agent/query
USERS: /api/users           (ya existe, usado para selector)

---

## Contrato API

### GET /api/reports/templates
Response: Template[]
Template {
  id: number,
  name: string,
  schedule: string[],
  recipients: string[],       # Resuelto desde pivote + users (telefonos actuales)
  recipient_ids: number[],    # IDs de usuarios seleccionados
  metrics: string[],
  is_active: boolean,
  created_at: string|null,
  updated_at: string|null
}

### POST /api/reports/templates
Request body: {
  name: string (min 1, max 255),
  schedule: string[],
  user_ids: number[],         # IDs de usuarios destinatarios
  metrics: string[],
  is_active: boolean (default true)
}
Response: Template (con recipients resueltos + recipient_ids)

### PUT /api/reports/templates/{template_id}
Request body: {
  name?: string,
  schedule?: string[],
  user_ids?: number[],        # IDs de usuarios destinatarios
  metrics?: string[],
  is_active?: boolean
}
Response: Template
Error: 404 { detail: Plantilla {id} no encontrada }

### DELETE /api/reports/templates/{template_id}
Response: 204 No Content
Error: 404 { detail: Plantilla {id} no encontrada }

### GET /api/anomalies/history (con paginacion)
Query params: page=1 (default), page_size=20 (default, max 100)
Response: {
  items: AnomalyLog[],
  total: number,
  page: number,
  page_size: number,
  total_pages: number
}
AnomalyLog { id, record_id, layer, z_score, metric_value, threshold, llm_report, sent_sms, created_at }

### GET /api/anomalies (Detectar ahora)
Query params: window=120 (default), threshold=3.0 (default), tipo_cosecha (opcional)
Response: AnomalyResult[] con record_id, layer, z_score, metric_value, threshold, detail

### POST /api/agent/query
Request: { query: string (min 1, max 1000) }
Response: { response: string, dev_mode: boolean }
Error: 503 { detail: LLM error... }

---

## Persistencia

### Tabla nueva: report_template_users (pivote)
| Columna     | Tipo             | Nullable | Default | Notas                                   |
|-------------|------------------|----------|---------|-----------------------------------------|
| template_id | BIGINT UNSIGNED  | NO       |         | FK -> report_templates.id, ON DELETE CASCADE |
| user_id     | BIGINT UNSIGNED  | NO       |         | FK -> users.id, ON DELETE CASCADE       |

**PK compuesta:** (template_id, user_id) - evita duplicados.
**Indices:** (user_id) para JOIN eficiente.

### Tabla modificada: report_templates
Se ELIMINA la columna recipients (TEXT). Los destinatarios ahora se almacenan
como filas en report_template_users.

### Migraciones
1. database/migrations/2026_07_08_000001_create_report_template_users_table.py
   - CREATE TABLE report_template_users
   - ALTER TABLE report_templates DROP COLUMN recipients

---

## Alternativas descartadas

### Alternativa A: Chat via WebSocket
Se descarto porque el endpoint POST /api/agent/query existente ya implementa
el flujo completo sobre REST. Migrar a WebSocket no aporta beneficio para
una consola admin de uso esporadico.

### Alternativa B: JSON de telefonos en columna recipients (reemplazado)
Almacenar destinatarios como JSON array de telefonos. Se descarto porque:
- Los telefonos se desincronizan si un usuario cambia su numero
- Viola normalizacion de datos
- No permite consultas SQL directas
La tabla pivote report_template_users resuelve estos problemas.

---

## Analisis de impacto en features existentes

### Feature 7 (sms_service)
| Item | Archivo | Cambio |
|------|---------|--------|
| _send_template_reports | src/sms_service.py | Cambiar lectura de template.recipients (JSON) por JOIN a report_template_users + users |

### Features 14, 15, 16 (Frontend admin)
Sin impacto directo. Los cambios son solo en TemplateFormModal.svelte y backend.

### Feature 8 (ai_agent)
GET /api/anomalies/history: response cambia a PaginatedResponse.

---

## Impacto en APIs existentes

### Feature 7 - report_templates
Los endpoints de reportes cambian su input/output:
- POST/PUT ahora aceptan user_ids en vez de recipients
- GET ahora incluye recipient_ids ademas de recipients (resuelto)

### Frontend
TemplateFormModal.svelte: reemplazar input de texto por selector de usuarios
con checkboxes (filtrados por roles admin y corresponsal, activos).
