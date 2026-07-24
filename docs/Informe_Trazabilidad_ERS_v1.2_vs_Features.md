# Informe de Trazabilidad — ERS v1.2 (Contrato) vs Funcionalidades Desarrolladas

*Proyecto: SIP-Edge — Sistema Inteligente de Pesaje y Control de Materia Extraña*
*Fecha: Julio 2026*
*Propósito: Comparar el alcance contratado (ERS v1.2, 11-Feb-2026) contra las funcionalidades reales entregadas*

---

## 1. Alcance Contratado — ERS v1.2

El documento ERS v1.2 define **21 Requisitos Funcionales (RF-001 a RF-021)** y **8 Requisitos No Funcionales (RNF-001 a RNF-008)**. De estos, RF-011, RF-016 y RF-019 son `[Should Have]`; el resto son `[Must Have]`.

### RF contratados (ERS v1.2)

| ID | Prioridad | Descripción resumida |
|----|-----------|---------------------|
| RF-001 | Must Have | Autenticación por credenciales con hash bcrypt |
| RF-002 | Must Have | RBAC: admin, operator, corresponsal |
| RF-003 | Must Have | Interacción bidireccional con báscula (comando-respuesta, timeout 500ms-3000ms) |
| RF-004 | Must Have | Persistencia en MariaDB (peso, usuario, fecha, hora, tipo material, hacienda, suerte) |
| RF-005 | Must Have | Integridad transaccional (commit/rollback atómico) |
| RF-006 | Must Have | CRUD Haciendas con borrado lógico |
| RF-007 | Must Have | Gestión de Suertes vinculadas a Hacienda padre |
| RF-008 | Must Have | Selección en cascada Hacienda → Suerte |
| RF-009 | Must Have | Orquestador de consultas con AI Agent (Qwen 2.5 3B + Function Calling) |
| RF-010 | Must Have | Detección proactiva de anomalías (Z-score > 3, ventana 120 registros / 4 horas) |
| RF-011 | Should Have | Análisis SQL estructurado con Function Calling |
| RF-012 | Must Have | Envío de SMS vía módem GSM (comandos AT) |
| RF-013 | Must Have | Reportes programados (06:00, 14:00, 22:00, configurables) |
| RF-014 | Must Have | Alertas de seguridad (intentos de acceso no autorizado, sesión expirada) |
| RF-015 | Must Have | Configuración dinámica de puertos hardware (Admin UI) |
| RF-016 | Should Have | Prueba de conectividad serial/GSM |
| RF-017 | Must Have | Persistencia de configuración en config.yaml + carga automática tras reinicio |
| RF-018 | Must Have | Respaldo automático diario (dump.sql.gz, rotación FIFO 30 días) |
| RF-019 | Should Have | Exportación a medios externos (USB/SD) con verificación CRC32 |
| RF-020 | Must Have | Modo manual de emergencia (activación SMS: `MANUAL_ON`, máx. 15 min) |
| RF-021 | Must Have | CRUD de usuarios (nombre, documento, rol, estado) |

### RNF contratados (ERS v1.2)

| ID | Descripción |
|----|-------------|
| RNF-001 | Latencia UI < 200ms en eventos de peso |
| RNF-002 | Operación offline garantizada |
| RNF-003 | Recuperación ante fallos (systemd, watchdog 30s) |
| RNF-004 | Campo de peso readonly (solo modificable vía báscula o modo manual) |
| RNF-005 | Validación estricta de entradas (XSS) |
| RNF-006 | Prevención de inyección SQL (ORM parametrizado) |
| RNF-007 | Prevención de inyección de prompt (tool calls con schemas Pydantic) |
| RNF-008 | Credenciales en variables de entorno (permisos 600) |

---

## 2. Funcionalidades Desarrolladas — Correspondencia con ERS v1.2

### 2.1 Features que implementan requisitos contratados

| Feature ID | Nombre | RF/RNF contratados cubiertos | Estado |
|------------|--------|------------------------------|--------|
| F1 | system_config | RF-015, RF-016, RF-017 | Done |
| F2 | auth_rbac | RF-001, RF-002, RNF-005, RNF-006, RNF-008 | Done |
| F3 | user_management | RF-021 | Done |
| F4 | farm_lot_crud | RF-006, RF-007, RF-008 | Done |
| F5 | scale_integration | RF-003 | Done |
| F6 | weighing_capture | RF-004, RF-005, RNF-004 | Done |
| F7 | sms_service | RF-012, RF-013, RF-014, RNF-002 | Done |
| F8 | ai_agent | RF-009, RF-010, RF-011, RNF-007 | Done |
| F9 | emergency_mode | RF-020 | Done |
| F10 | backup_system | RF-018, RF-019 | Done |
| — | Infraestructura | RNF-001, RNF-002, RNF-003, RNF-005, RNF-006, RNF-007, RNF-008 | Transversal |

### 2.2 Frontend — Capa de UI para requisitos contratados

Estas features implementan la interfaz de usuario requerida por los RF. No introducen nuevos RF sino que materializan los ya contratados.

| Feature ID | Nombre | RF contratados que implementa en UI | Estado |
|------------|--------|-------------------------------------|--------|
| F13 | frontend_login_kiosk | RF-001, RF-002, RF-003, RF-004, RF-005, RF-020 | Done |
| F14 | frontend_admin_dashboard | RF-002 (vista admin, navegación RBAC) | Done |
| F15 | frontend_admin_operations | RF-015, RF-016, RF-017 (config UI) + RF-018, RF-019 (backup UI) | Done |
| F16 | frontend_admin_masterdata | RF-006, RF-007, RF-021 (CRUD UI) | Done |
| F17 | frontend_analytics | RF-009, RF-010, RF-011 (reportes, anomalías, consola IA) | Done |

### 2.3 Bugs corregidos (implementación, no requisitos)

Estos items documentan errores corregidos durante el desarrollo. No constituyen funcionalidades nuevas ni requisitos adicionales.

| Bug ID | Nombre | Afectaba RF | Estado |
|--------|--------|-------------|--------|
| F19 | Watchdog mal configurado — reinicio cada 30s | RNF-003 | Done |
| F20 | AdminSuertes.svelte no carga suertes | RF-008 | Done |
| F22 | Campo phone no expuesto + campo document ambiguo | RF-021, RF-020, RF-030 | Done |
| F23 | Modo manual no se activa vía SMS | RF-020 | Done |
| F26 | Solicitud emergencia kiosko envía mensaje de error LLM | RF-020 | Done |
| F29 | ScaleService async reader crashes + WebSocket | RF-003 | Done |
| F30 | Watchdog mata proceso cada 30s (sd_notify) | RNF-003 | Done |
| F31 | Dispatcher v2 crashea en get_user_role_by_phone | RF-012, RF-020, RF-030 | Done |
| F40 | Session timeout mide edad del token, no inactividad real | RF-002 (sesión) | Done |

---

## 3. Features Adicionales — Fuera del Alcance Contratado

Las siguientes funcionalidades fueron desarrolladas e incorporadas al sistema **sin estar contempladas en el ERS v1.2 original**. No tienen correspondencia con ningún RF o RNF del contrato.

### 3.1 Transmisión RS232 y Restablecimiento de Contraseña

Estas dos features fueron las primeras extensiones significativas, documentadas posteriormente en el ERS v1.3 como RF-022 y RF-030.

| Feature ID | Nombre | Descripción | RF equivalente (ERS v1.3+) |
|------------|--------|-------------|---------------------------|
| **F11** | rs232_transmission | Envío de trama CSV con 15 campos al PC externo vía RS232 tras cada pesaje confirmado. Formato fijo con terminación CRLF. | RF-022 |
| **F12** | password_reset_sms | Restablecimiento remoto de contraseña vía SMS. Admin envía `reset password <usuario>`, sistema genera PIN de 4 dígitos (válido 1h), analista lo ingresa en modal del login. | RF-030 |

### 3.2 Expansiones sobre features contratadas

Algunas features contratadas se expandieron más allá de lo especificado en ERS v1.2. Las porciones adicionales se listan aquí:

| Feature ID | Nombre | Alcance contratado (ERS v1.2) | Expansión adicional |
|------------|--------|-------------------------------|---------------------|
| **F2** | auth_rbac | RF-001, RF-002 | **Bloqueo por inactividad**: timeout de sesión configurable en `config.yaml` (RF-026 en ERS v1.3). No contemplado en v1.2. |
| **F8** | ai_agent | RF-009, RF-010, RF-011 | **Catálogo de 12 herramientas SQL** parametrizadas (RF-027), **detección en 3 capas** (Z-Score + ratios + temporal, RF-028), **CPU pinning** con taskset para llama-server (RF-029). ERS v1.2 solo pedía orquestador genérico + Z-score simple. |
| **F9** | emergency_mode | RF-020: comando SMS `MANUAL_ON`, máx. 15 min | **Flujo completo**: solicitud desde kiosko con modal + selección de supervisor + motivo obligatorio + SMS de solicitud + aprobación remota + extensiones de tiempo + suspensión anticipada + persistencia ante cortes + múltiples solicitudes simultáneas + auditoría en `emergency_mode_log`. |
| **F10** | backup_system | RF-018, RF-019 | **Tabla backup_logs** (RF-023), **endpoint GET /api/backup/status** (RF-024), **endpoint POST /api/backup/run** (RF-025). |

### 3.3 Mejoras de experiencia de usuario y operación

| Feature ID | Nombre | Descripción | Justificación |
|------------|--------|-------------|---------------|
| **F18** | harvest_type | Campo `tipo_cosecha` (Cosechadora / Cosecha manual) en tabla `weighings`. Select en formulario de kiosko. Filtro en análisis estadísticos. | Requerimiento operativo surgido durante pruebas de campo. |
| **F21** | pagination_users_backups | Paginación en endpoints y tablas de Usuarios y Backups. Formato `{items, total, page, page_size, total_pages}`. | Escalabilidad: 20-50+ usuarios y 40+ backups con rotación FIFO. |
| **F24** | reset_individual_pesos | 3 botones de reset individual (uno por cada campo de peso: muestra, mineral, vegetal) en lugar de un único botón Reset general. | Mejora de flujo de trabajo: permite corregir una sola lectura sin perder las otras dos. |
| **F36** | hacienda_search_filter | Campo de entrada de texto con autocompletado para código de hacienda. Sustituye dropdown `<select>`. Match exacto cliente-side con botón "Crear nueva hacienda" si no existe. | Agilidad para operadores con códigos memorizados. |
| **F37** | notas_muestras | Campo de texto colapsable para notas/observaciones del operador sobre cada medida. Persiste en columna `notas` de `weighings`. Consultable vía SMS. | Trazabilidad cualitativa: problemas con core sampler, muestras de empalme, observaciones visuales. |
| **F38** | operator_hacienda_suerte_crud | Pestañas [Haciendas] y [Suertes] en vista kiosko. Operadores pueden crear/editar (sin eliminar) haciendas y suertes directamente, sin requerir acceso al panel admin. | Autonomía del operador en campo. |
| **F39** | hacienda_suerte_created_by | Columna `created_by` (FK → users.id) en tablas `haciendas` y `suertes`. Trazabilidad de quién creó cada registro. | Auditoría y responsabilidad sobre datos maestros. |

### 3.4 Herramientas de desarrollo y pruebas

| Feature ID | Nombre | Descripción |
|------------|--------|-------------|
| **F25** | virtual_scale | Simulador de balanza DINI ARGEO DFW06L vía puerto serial. Carga datos desde CSV pre-generados (5 datasets, 250 medidas). Simula estabilidad (ST/US) con delays realistas. REPL interactivo con teclas n/p/w/g/s/q. Permite probar el ciclo completo de pesaje sin hardware físico. |

### 3.5 Infraestructura de persistencia y conversación SMS

| Feature ID | Nombre | Descripción |
|------------|--------|-------------|
| **F27** | sms_persistence | Tablas `sms_conversations` y `sms_messages` en MariaDB. Dispatcher v2 que persiste SMS entrantes/salientes con estado. Cola de envío asíncrona en thread separado (no bloquea uvicorn). Handlers de emergencia y password reset migrados a las nuevas tablas. SMS no reconocidos → respuesta de ayuda, sin caer en AI catch-all. |
| **F28** | ai_multi_turn | Conversación multiturno para consultas AI vía SMS. Contexto conversacional (últimos 10 exchanges) mantenido en `sms_conversations.metadata`. Tabla `sms_ai_tool_log` para auditoría de tool_calls. Sin timeout de inactividad; la conversación se mantiene hasta despedida o límite FIFO de 10 exchanges. |

### 3.6 Herramientas estadísticas v2

| Feature ID | Nombre | Descripción |
|------------|--------|-------------|
| **F33** | sql_tools_v2 | 4 nuevas herramientas SQL + 3 modificadas. Shortcuts de fecha (hoy, ayer, últimos 7 días, mes actual). Parámetros de agrupación (día/semana/mes/turno). Filtro por vehículo. Nuevas métricas: `get_avg_weighing_time`, `get_anomaly_rate`, `get_top_haciendas`, `get_period_comparison`. Setup card "Límites de Control". Desviación estándar en reportes SMS. |

---

## 4. Resumen de Cobertura

### 4.1 Requisitos contratados: cobertura completa

| Categoría | Total | Cubiertos | Features que los implementan |
|-----------|-------|-----------|------------------------------|
| RF Must Have (ERS v1.2) | 18 | 18 (100%) | F1–F10 |
| RF Should Have (ERS v1.2) | 3 | 3 (100%) | F1, F8, F10 |
| RNF (ERS v1.2) | 8 | 8 (100%) | Transversal (F2, F5, F6, F7, F8, infraestructura) |
| **Total contratado** | **29** | **29 (100%)** | |

### 4.2 Funcionalidades adicionales

| Categoría | Cantidad | Features |
|-----------|----------|----------|
| Nuevas funcionalidades completas (sin RF en ERS v1.2) | 2 | F11, F12 |
| Expansiones sobre features contratadas | 4 | Ampliaciones en F2, F8, F9, F10 |
| Mejoras de UX y operación | 6 | F18, F21, F24, F36, F37, F38, F39 |
| Infraestructura y herramientas | 4 | F25, F27, F28, F33 |
| **Total adicionales** | **16** | |

### 4.3 Bugs corregidos

| Cantidad | IDs |
|----------|-----|
| 9 | F19, F20, F22, F23, F26, F29, F30, F31, F40 |

---

## 5. Notas

1. **Todas las funcionalidades contratadas en ERS v1.2 están implementadas y verificadas.** No hay RF contratado sin cubrir.

2. **Las features adicionales (Sección 3)** no forman parte del alcance contratado. Fueron incorporadas durante el ciclo de desarrollo como respuesta a necesidades operativas detectadas en pruebas de campo (F18, F24, F36, F37, F38, F39), mejoras de infraestructura para robustez (F25, F27, F28), o extensiones de analítica (F33). Se documentan aquí para trazabilidad pero no deben considerarse como parte del entregable contractual.

3. **El ERS v1.3 (16-Jun-2026)** recoge las expansiones F11 (RF-022), F12 (RF-030), y las ampliaciones de F2 (RF-026), F8 (RF-027/028/029) y F10 (RF-023/024/025). Los RF-V14-XX del ERS v1.4 corresponden a features posteriores (F33, y las pendientes F34, F35, F32).

4. **Las features pendientes (F32, F34, F35)** no se incluyen en este informe por estar fuera del alcance contratado y constituir mejoras propuestas aún no aprobadas.

5. **El frontend (F13–F17)** se implementó como SPA en Svelte 5 (no en HTML5 + HTMX como sugería el ERS v1.2). Esta decisión de diseño no altera el cumplimiento de los RF contratados.

---

*Documento generado a partir del análisis de `harness/feature_list.json`, ERS v1.2, y los specs en `harness/specs/`.*
