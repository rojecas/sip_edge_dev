# Feature 17 — Frontend Analytics: Design

## Resumen

Feature 100% frontend (Svelte 5) que consume endpoints de backend existentes de las features 8 (ai_agent) y 7 (sms_service). Agrega tres nuevas vistas administrativas: Reportes Programados (CRUD de plantillas), Historial de Anomalías (tabla paginada) y Consola del Agente IA (chat). Requiere modificaciones mínimas al backend para agregar paginación a GET /api/anomalies/history.

---

## Archivos a crear

| Archivo | Propósito |
|---------|-----------|
| `frontend/src/components/AdminReportes.svelte` | Vista CRUD de plantillas de reportes |
| `frontend/src/components/TemplateFormModal.svelte` | Modal de creación/edición de plantilla |
| `frontend/src/components/AdminAnomalias.svelte` | Vista de historial de anomalías paginado |
| `frontend/src/components/AdminAgente.svelte` | Interfaz tipo chat para consultas al agente |

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `frontend/src/App.svelte` | Agregar imports y condicionales de ruta para `/admin/reportes`, `/admin/anomalias`, `/admin/agente` |
| `frontend/src/components/AdminLayout.svelte` | Agregar links al sidebar para Reportes, Anomalías, Agente |
| `frontend/src/components/AdminDashboard.svelte` | Agregar cards de acceso rápido para las 3 nuevas secciones |
| `frontend/src/lib/constants.js` | Agregar constantes `REPORTS_TEMPLATES`, `ANOMALIES_HISTORY`, `ANOMALIES_DETECT`, `AGENT_QUERY` |
| `src/main.py` | Refactorizar `GET /api/anomalies/history` para soportar paginación con `page` y `page_size` |

---

## Firmas nuevas (frontend)

### Componentes Svelte

```
AdminReportes.svelte
  Props: ninguna (self-contained)
  State interno: plantillas[], loading, loadError, emptyMsg, formShow, formMode, formPlantilla

TemplateFormModal.svelte
  Props: show: boolean, mode: "create"|"edit", plantilla: object|null, error: string,
         onClose: () => void, onSave: (payload: object) => Promise<void>
  State interno: form { name, schedule[], recipients[], metrics[], is_active }

AdminAnomalias.svelte
  Props: ninguna (self-contained)
  State interno: anomalias[], loading, loadError, currentPage, totalPages, pageSize

AdminAgente.svelte
  Props: ninguna (self-contained)
  State interno: messages[{role, content}], inputText, loading, error
```

### Nuevas constantes en `constants.js`

```javascript
REPORTS_TEMPLATES: "/api/reports/templates",
REPORTS_TEMPLATES_BY_ID: "/api/reports/templates/",
ANOMALIES_HISTORY: "/api/anomalies/history",
ANOMALIES_DETECT: "/api/anomalies",
AGENT_QUERY: "/api/agent/query",
```

---

## Modificaciones al backend (`src/main.py`)

### GET /api/anomalies/history — Agregar paginación

Se modifica el endpoint existente para aceptar parámetros `page` (default 1) y `page_size` (default 20, max 100) y devolver `PaginatedResponse` en lugar de array plano. Se mantiene el parámetro `limit` como alias de `page_size` para compatibilidad parcial (documentado como deprecado).

---

## Contrato API

### GET /api/reports/templates
```
Response: Template[]
Template {
  id: number,
  name: string,
  schedule: string[],
  recipients: string[],
  metrics: string[],
  is_active: boolean,
  created_at: string|null,
  updated_at: string|null
}
```

### POST /api/reports/templates
```
Request body: {
  name: string (min 1, max 255),
  schedule: string[],
  recipients: string[],
  metrics: string[],
  is_active: boolean (default true)
}
Response: Template (id, name, schedule, recipients, metrics, is_active)
```

### PUT /api/reports/templates/{template_id}
```
Request body: {
  name?: string,
  schedule?: string[],
  recipients?: string[],
  metrics?: string[],
  is_active?: boolean
}
Response: Template
Error: 404 { detail: "Plantilla {id} no encontrada" }
```

### DELETE /api/reports/templates/{template_id}
```
Response: 204 No Content
Error: 404 { detail: "Plantilla {id} no encontrada" }
```

### GET /api/anomalies/history (modificado con paginación)
```
Query params: page=1 (default), page_size=20 (default, max 100)
Response: {
  items: AnomalyLog[],
  total: number,
  page: number,
  page_size: number,
  total_pages: number
}
AnomalyLog {
  id: number,
  record_id: number,
  layer: string,
  z_score: number|null,
  metric_value: number,
  threshold: number,
  llm_report: string|null,
  sent_sms: boolean,
  created_at: string|null
}
```

### GET /api/anomalies (Detectar ahora)
```
Query params: window=120 (default), threshold=3.0 (default), tipo_cosecha (opcional)
Response: AnomalyResult[]
AnomalyResult {
  record_id: number,
  layer: string,
  z_score: number|null,
  metric_value: number,
  threshold: number,
  detail: string
}
```

### POST /api/agent/query
```
Request body: { query: string (min 1, max 1000) }
Response: { response: string, dev_mode: boolean }
Error: 503 { detail: "LLM error: ..." }
```

---

## Persistencia

No se requieren cambios en la base de datos. Esta feature es únicamente de interfaz de usuario. Las tablas `report_templates` y `anomaly_log` ya existen y son gestionadas por features 8 y 7.

---

## Alternativa descartada

**Chat vía WebSocket en lugar de REST para la consola del agente.**
Se descartó porque el endpoint `POST /api/agent/query` existente ya implementa el flujo completo (LLM → tool_calls → respuesta) sobre REST. Migrar a WebSocket requeriría reescribir el orquestador del agente y no aporta beneficio significativo para una consola admin de uso esporádico. REST es más simple, testeable y consistente con el resto de la API.

---

## Análisis de impacto en features existentes

### Feature 14 (frontend_admin_dashboard) — Dashboard y Navegación

| Ítem | Archivo | Cambio |
|------|---------|--------|
| AdminLayout.svelte | `frontend/src/components/AdminLayout.svelte` | Agregar 3 nuevos links al array `links[]` (Reportes, Anomalías, Agente) |
| AdminDashboard.svelte | `frontend/src/components/AdminDashboard.svelte` | Agregar 3 nuevas cards al array `cards[]` |
| App.svelte | `frontend/src/App.svelte` | Agregar 3 nuevas condiciones de ruta e imports de componentes |

**Compatibilidad hacia atrás:** Total. Solo se agregan entradas a arrays existentes. No se modifica interfaz de componentes.

### Feature 15 (frontend_admin_operations) — Config y Backup

Sin impacto. Esta feature no toca `AdminConfig`, `AdminBackup` ni sus archivos asociados.

### Feature 16 (frontend_admin_masterdata) — CRUD Datos Maestros

Sin impacto directo sobre componentes de usuarios, haciendas o suertes. Los nuevos componentes (`AdminReportes`, `AdminAnomalias`, `AdminAgente`) son independientes.

### Feature 8 (ai_agent) — Sistema Inteligente

| Ítem | Archivo | Cambio |
|------|---------|--------|
| GET /api/anomalies/history | `src/main.py` | Cambio de response de array plano a `PaginatedResponse`. **Rompe compatibilidad hacia atrás** con consumidores que esperen array directo. |

**Plan de mitigación:** El endpoint `GET /api/anomalies/history` actualmente solo es consumido desde test y desde el futuro frontend de esta misma feature. No hay clientes externos. Se documenta el cambio en el contrato API. Ningún otro endpoint de feature 8 se modifica.

### Feature 7 (sms_service)

Sin impacto. Los endpoints de plantillas de reportes (`/api/reports/templates`) ya existen y no se modifican.

---

## Impacto en APIs existentes

### Feature 8 — ai_agent

| Endpoint | Cambio | Justificación |
|----------|--------|---------------|
| GET /api/anomalies/history | Response cambia de `AnomalyLog[]` a `PaginatedResponse<AnomalyLog>` | Necesario para paginación en frontend. El formato `PaginatedResponse` ya está definido en `src/schemas.py` y es el estándar del proyecto (usado por users, haciendas, suertes, backups). |

### Frontend

No hay impacto en componentes frontend existentes. Los nuevos componentes son independientes y se integran mediante el sistema de rutas existente.
