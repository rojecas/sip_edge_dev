# Especificación de Requisitos de Software (ERS) – Versión 1.3
*Proyecto: Sistema Inteligente de Pesaje y Control de Materia Extraña (SIP-Edge)*
*Plataforma: EdgeBox RPi-200 (8GB RAM / 32GB eMMC), Raspberry Pi OS x64*
*Fecha: 16-Jun-2026*
*Cambios v1.3: Integración de todos los requisitos descubiertos durante el ciclo de desarrollo SDD de las 12 features. Refleja el sistema real implementado.*

---

## 1. Introducción

### 1.1 Propósito
El propósito de este documento es definir los requisitos funcionales y no funcionales para el desarrollo del **Sistema Inteligente de Pesaje y Control de Materia Extraña (SIP-Edge)**. Este sistema integra lectura de hardware industrial (báscula vía RS485) con envío de datos a PC externo vía RS232, un Agente de Inteligencia Artificial (TinyLLM) para detección de anomalías y reportes automatizados vía SMS, y un sistema completo de gestión de accesos, usuarios y respaldos.

### 1.2 Alcance
El sistema funciona como una solución *standalone* desplegada en el laboratorio de cañas. Gestiona:

- Captura y almacenamiento de registros de peso (caña y materia extraña) con autenticación por credenciales.
- Análisis de datos mediante Agente IA para detección de anomalías estadísticas en 3 capas.
- Notificaciones automatizadas vía SMS (reportes programados configurables y alertas de seguridad).
- Gestión de usuarios con Control de Acceso Basado en Roles (RBAC).
- Transmisión de datos de pesaje a PC externo vía RS232 en formato CSV fijo.
- Restablecimiento remoto de contraseñas vía SMS con PIN temporal de un solo uso.
- Sistema de respaldos automáticos con rotación y exportación a medios externos.
- Modo manual de emergencia con activación remota vía SMS y solicitud desde kiosco.
- Detección de anomalías en 3 capas (Z-Score, ratios entre materiales, tasa de cambio temporal) con invocación de LLM bajo demanda.

### 1.3 Contexto y Justificación de la Solución

#### 1.3.1 Situación Actual
El laboratorio de cañas opera como una "isla de información" dentro de la planta, con reportes de materia extraña vía email o comunicación verbal bajo demanda, y registro de datos fuera de línea. El sistema Legacy presenta:

- Brechas de seguridad en validación de identidad durante el registro de pesos.
- Pérdida de información por borrado accidental de base de datos.
- Detección manual y reactiva de anomalías de peso.

#### 1.3.2 Valor Aportado por la Solución
- **Integridad Operativa**: Autenticación robusta por credenciales + RBAC + bloqueo por inactividad.
- **Inteligencia en el Borde (Edge AI)**: Sistema de 3 capas de detección de anomalías con LLM para reportes narrativos bajo demanda.
- **Conectividad Resiliente**: Notificaciones SMS vía módulo GSM con capacidad de consulta ad-hoc y comandos remotos.
- **Continuidad Operativa**: Modo manual de emergencia con activación remota y respaldos automáticos.

### 1.4 Definiciones, Acrónimos y Abreviaturas

| Término | Definición |
|---------|------------|
| **SIP-Edge** | Sistema Inteligente de Pesaje y Control de Materia Extraña |
| **TinyLLM** | Modelo de Lenguaje Pequeño (SLM) optimizado para dispositivos edge (Qwen 2.5 1.5B GGUF) |
| **RBAC** | Role-Based Access Control (Control de Acceso Basado en Roles) |
| **GSM** | Global System for Mobile Communications (módulo de comunicación celular) |
| **eMMC** | Embedded MultiMediaCard (almacenamiento integrado de 32GB) |
| **RS485** | Puerto serial industrial para comunicación con báscula DINI ARGEO DFWLI-2 |
| **RS232** | Puerto serial para transmisión de datos a PC externo |
| **Function Calling** | Mecanismo por el cual el LLM invoca herramientas predefinidas en lugar de generar texto libre |
| **Z-Score** | Medida estadística de desviación respecto a la media, expresada en desviaciones estándar |
| **SDD** | Spec Driven Development — metodología de desarrollo basada en especificaciones |
| **RF** | Requisito Funcional |
| **RNF** | Requisito No Funcional |

### 1.5 Referencias
- Manual de Protocolo de Comunicación de Báscula DINI ARGEO DFWLI-2 — `docs/Balance_Comm_protocol.md`
- Especificación Técnica Qwen 2.5 1.5B (GGUF)
- Documento de Instalación de llama.cpp — `docs/Instalacion de llama.cpp.md`
- Documento de Configuración de Hardware — `docs/Informe 01 - Configuracion de Hardware.md`
- Documento de Configuración de Entorno — `docs/Informe 02 - Configuracion del Entorno de Ejecucion.md`

---

## 2. Descripción General

### 2.1 Perspectiva del Proyecto
El sistema opera en la capa de *Edge Computing*. Interactúa con:

- **Hardware de Proceso**: Báscula DINI ARGEO DFWLI-2 vía RS485 (comando-respuesta) y PC externo vía RS232 (envío de tramas CSV).
- **Hardware de Comunicación**: Módulo GSM Quectel EC25 mini PCIe para envío y recepción de SMS.
- **Motor de IA**: llama.cpp con Qwen 2.5 1.5B Q4_K_M en 3 cores dedicados (taskset -c 0-2).
- **Usuarios**: Operador (presencial), Corresponsal/Gerente (remoto vía SMS), Administrador (configuración).

### 2.2 Características de los Usuarios
- **Analista/Operador de Laboratorio**: Autenticación por credenciales. Flujo de pesaje en 3 pasos (tara + lectura de muestra, mineral, vegetal). Puede solicitar modo manual de emergencia.
- **Corresponsal/Gerente**: Recibe reportes programados y alertas vía SMS. Puede consultar datos mediante SMS en lenguaje natural.
- **Supervisor/Administrador**: Acceso total a configuración, gestión de usuarios, respaldos. Puede autorizar modo manual y restablecer contraseñas vía SMS.

### 2.3 Restricciones Generales
- **Hardware**: EdgeBox RPi-200 (8GB RAM, 32GB eMMC, CPU ARM Cortex-A72, 4 cores).
- **CPU Pinning**: 3 cores (0-2) dedicados a llama-server mediante taskset. Core 3 para backend y BD.
- **Respaldo Eléctrico**: Power bank en línea (10.000-25.000 mAh).
- **Conectividad**: Operatividad 100% offline garantizada (solo SMS requiere señal GSM).
- **Ambiente**: Industrial (polvo, vibración, iluminación variable).

### 2.4 Suposiciones y Dependencias
- `[D-001]` **Protocolo de Báscula**: Báscula DINI ARGEO DFWLI-2 configurada en modo RS-485 con dirección "00".
- `[D-002]` **Cobertura GSM**: Envío y recepción de SMS depende de señal celular 3G/4G (>85% uptime esperado).
- `[D-003]` **Modelo LLM**: Qwen 2.5 1.5B Instruct GGUF Q4_K_M disponible en `/home/models/`. Consumo <2GB RAM.

### 2.5 Requisitos de Interfaz Externa

#### 2.5.1 Interfaces de Usuario (UI)
- **Estilo Kiosco**: Diseñada para pantallas ≥13" con teclado y mouse.
- **Feedback Visual**: Códigos de color universales (Verde=Éxito, Rojo=Error, Amarillo=Procesando).
- **Login**: Pantalla con usuario + contraseña + enlace "Olvidó su contraseña" que abre modal de PIN + modal de cambio de contraseña.
- **Kiosco de Pesaje**: Formulario con selección en cascada de Hacienda+Suerte, campos tractomula/vagon/guia, 3 pares Tara+Leer (muestra, mineral, vegetal), botón Confirmar y Reset.
- **Configuración Admin**: Interfaz para gestión de puertos, usuarios, haciendas, suertes, plantillas de reporte y respaldos.

#### 2.5.2 Interfaces de Hardware

| Puerto/Socket | Asignación | Protocolo | Notas |
|---------------|------------|-----------|-------|
| USB 1 | Mouse y teclado | — | Único puerto USB requerido |
| **RS485** | Báscula DINI ARGEO DFWLI-2 | `/dev/ttyACM0` | Comunicación comando-respuesta (115200 8N1) |
| **RS232** | PC Externo | `/dev/ttyACM1` | Envío de tramas CSV de pesaje (115200 8N1) |
| mini PCIe | Módulo GSM Quectel EC25 | `/dev/ttyUSB2`, `/dev/ttyUSB3` | Gestión via ModemManager (`mmcli -m 0`) |
| M.2 | *Sin asignar* | — | Reservado para NVMe en future scope |

#### 2.5.3 Interfaces de Software
- **Sistema Operativo**: Debian 13 (Trixie) aarch64, kernel 6.12.
- **Base de Datos**: MariaDB 11.8.6 (motor InnoDB).
- **Runtime**: Python 3.13+ con FastAPI + SQLAlchemy.
- **Motor IA**: llama.cpp b9632, servidor en puerto localhost:8080.
- **Gestión SMS**: ModemManager + mmcli.

---

## 3. Requisitos Funcionales (RF)

### 3.1 Módulo de Autenticación, RBAC y Seguridad

`[RF-001]` **[Must Have]** Autenticación por Credenciales:
El sistema valida identidad mediante usuario/contraseña con hash bcrypt y emite token JWT.
Incluye:
- Hash de contraseña con bcrypt.
- Token JWT con expiración configurable.
- Endpoint `POST /api/auth/login` que retorna token + datos del usuario.
- Protección de endpoints mediante dependencia JWT (`check_inactivity`, `require_role`).

`[RF-002]` **[Must Have]** Control de Acceso Basado en Roles (RBAC):
Restricción de funcionalidades según rol:
- *admin*: Acceso total (configuración, usuarios, respaldos, reportes).
- *operator*: Solo formulario de pesaje y registros del turno actual.
- *corresponsal*: Recepción/envío de SMS (sin login al sistema).

`[RF-026]` **[Must Have]** Bloqueo por Inactividad:
El sistema fuerza re-login si el usuario no presenta actividad dentro del timeout configurable
en `config.yaml` (sección `session`). Timeout default: 30 minutos.

### 3.2 Módulo de Pesaje, Báscula y Transmisión

`[RF-003]` **[Must Have]** Interacción Bidireccional con Báscula (RS485):
Protocolo activo sobre RS485 donde el sistema:
- Envía comandos al puerto `/dev/ttyACM0` al presionar botones: `REXT` (lectura completa),
  `TARE` (tara semiautomática), `TMAN` (tara manual), `ZERO` (reset), `CLEAR` (limpiar tara).
- Espera respuesta con timeout configurable 1-10s (default 3s).
- Escucha asíncrona de datos entrantes desde la balanza (botón PRINT físico de la báscula).

`[RF-004]` **[Must Have]** Persistencia de Datos (Pesaje):
Almacenamiento en MariaDB tabla `weighings` con campos: id, fecha, hora, tractomula, vagon,
numero_guia, hacienda_id, suerte_id, peso_muestra (Numeric 10,3), peso_mineral (Numeric 10,3),
peso_vegetal_extrano (Numeric 10,3), usuario_id, created_at, enviado_pc (Boolean), manual_entry (Boolean).

`[RF-005]` **[Must Have]** Integridad Transaccional:
Registro de pesaje y metadata como transacción atómica única (commit/rollback vía SQLAlchemy).
El envío RS232 no debe interrumpir la transacción principal.

`[RF-006]` **[Must Have]** Gestión de Haciendas:
Interfaz Admin para Crear/Editar/Desactivar (borrado lógico con `deleted_at`).
Sin eliminación física si existen registros asociados en `weighings`.

`[RF-007]` **[Must Have]** Gestión de Suertes/Lotes:
Gestión obligatoriamente vinculada a Hacienda padre (FK `hacienda_id`).
Unique constraint: `(hacienda_id, codigo_suerte)`.

`[RF-008]` **[Must Have]** Selección en Cascada:
Carga dinámica de Suertes según Hacienda seleccionada en el formulario de pesaje.
Endpoint `GET /api/suertes?hacienda_id=X` retorna solo suertes activas (sin `deleted_at`).

`[RF-022]` **[Must Have]** Transmisión de Datos a PC vía RS232:
El sistema envía tramas de información estructurada al PC externo a través del puerto RS232
configurado (`/dev/ttyACM1`). La transmisión se dispara automáticamente cuando el analista
oprime el botón [confirmar medida] en el kiosco de pesaje y el endpoint retorna status 201.

Formato fijo CSV con 15 campos separados por coma y terminación CRLF:
```
Id,Fecha,Hora,Vagon,Guía,Peso_muestra,0,0,0,0,0,0,0,Peso_vegetal,Peso_mineral
```
- Vagon: identificador alfanumérico del vagón (se envía tal cual del registro).
- Campos 7-13: padding fijo de 7 ceros (no reemplazar).
- Pesos: formateados con 3 decimales.

Si el envío falla, se registra el error vía logging pero el pesaje permanece confirmado
en BD. El campo `enviado_pc` se actualiza a True solo si el envío fue exitoso.

### 3.3 Agente de Orquestación, Reportería y Análisis (TinyLLM)

`[RF-009]` **[Must Have]** Sistema de Reportería Programada Configurable:
El administrador puede crear plantillas de reporte programado seleccionando qué métricas
incluir entre las siguientes opciones:
- `count` — Cantidad de pesajes en el período.
- `total_weight` — Peso total (muestra + mineral + vegetal).
- `avg_weight` — Peso promedio por pesaje.
- `min_max_weight` — Peso mínimo y máximo del período.
- `breakdown_by_hacienda` — Desglose de pesaje por hacienda.
- `breakdown_by_operator` — Desglose de pesaje por operador.
- `material_composition` — Proporción muestra / mineral / vegetal.
- `anomaly_count` — Cantidad de anomalías detectadas en el período.
- `trend` — Tendencia del período (pendiente de regresión lineal).

Los reportes se envían vía SMS a la lista de corresponsales en horarios configurables
(por defecto 06:00, 14:00, 22:00). La generación del reporte es puramente SQL + plantilla
(sin invocar el LLM).

`[RF-010]` **[Must Have]** Detección de Anomalías en 3 Capas:
Tras cada pesaje confirmado, el sistema ejecuta detección en 3 capas secuenciales:

**Capa 1 — Z-Score con ventana móvil:**
- Ventana: últimos 120 registros o últimas 4 horas (lo que ocurra primero), configurable.
- Cálculo: Z = |peso_total - media_ventana| / desv_estándar_ventana.
- Umbral: |Z| > 3.0 (configurable).
- Si std == 0, no se detecta anomalía.

**Capa 2 — Filtro relacional (ratios entre materiales):**
- Ratio vegetal/muestra: Si vegetal_extrano > 50% de peso_muestra → anomalía.
- Ratio mineral/muestra: Si mineral > 30% de peso_muestra → anomalía.
- Umbrales configurables.

**Capa 3 — Filtro temporal:**
- Tasa de cambio: Si |peso_actual - peso_anterior| / peso_anterior > 50% → anomalía.
- Rachas: Si 3+ pesajes consecutivos superan el umbral Z → anomalía sistémica.
- Umbrales configurables.

`[RF-011]` **[Should Have]** Consultas Ad-Hoc vía SMS con Function Calling:
Un corresponsal puede enviar un SMS con una pregunta en lenguaje natural sobre los datos
recopilados (ej: "cómo va el turno de hoy"). El sistema:
1. Recibe el SMS via el IncomingSmsDispatcher.
2. Envía la pregunta al LLM (Qwen 2.5 1.5B) con catálogo de herramientas SQL disponibles.
3. El LLM responde con una llamada a función específica (tool_call).
4. El sistema ejecuta la herramienta SQL con datos reales de la BD.
5. Pasa el resultado al LLM para paráfrasis.
6. Envía la respuesta final por SMS al remitente.

El LLM NUNCA genera valores numéricos — solo parafrasea resultados de herramientas ejecutadas.

`[RF-027]` **[Must Have]** Catálogo de Herramientas Estadísticas (SQL Tools):
El sistema expone las siguientes herramientas SQL parametrizadas para el LLM:
1. `get_basic_stats(fecha_inicio, fecha_fin, tipo_material)` — count, avg, min, max, std.
2. `get_percentiles(fecha_inicio, fecha_fin, percentil)` — percentil específico (P50, P95, P99).
3. `get_moving_average(window_size, tipo_material)` — promedio móvil.
4. `get_trend(fecha_inicio, fecha_fin, tipo_material)` — pendiente de regresión lineal.
5. `get_breakdown_by_hacienda(fecha_inicio, fecha_fin)` — agregado por hacienda.
6. `get_breakdown_by_operator(fecha_inicio, fecha_fin)` — agregado por operador.
7. `get_material_composition(fecha_inicio, fecha_fin)` — proporción muestra/mineral/vegetal.
8. `get_shift_summary(fecha, turno)` — reporte completo de turno (00-06, 06-14, 14-22).
9. `get_daily_summary(fecha)` — agregado diario.
10. `get_custom_period_summary(fecha_inicio, fecha_fin)` — resumen de período arbitrario.
11. `detect_anomalies(window_size, z_threshold)` — lista de anomalías detectadas.
12. `check_thresholds(window_size)` — evaluación de indicadores vs umbrales.

Todas las herramientas reciben parámetros tipados (nunca strings SQL concatenados).
Todas usan SQLAlchemy ORM (nunca SQL crudo).

`[RF-028]` **[Must Have]** Invocación del LLM ante Anomalía:
Si alguna de las 3 capas de detección detecta una anomalía, el sistema:
1. Lee contexto estadístico real (últimos N registros, media, desviación).
2. Invoca el LLM con el contexto para generar un reporte narrativo.
3. Envía el reporte por SMS a todos los corresponsales.
4. Registra la anomalía en la tabla `anomaly_log`.
5. Si el LLM falla (timeout, error de conexión), se registra el error y se envía
   una alerta SMS simple sin narrativa del LLM.

`[RF-029]` **[Must Have]** CPU Pinning para llama-server:
El proceso llama-server DEBE ejecutarse con:
```
taskset -c 0-2 llama-server -t 3 -m /home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf ...
```
- Cores físicos 0-2: exclusivos para inferencia LLM.
- Core 3: backend FastAPI + MariaDB + servicios.
- Configurado via systemd service con `CPUSchedulingPolicy=rr` y `CPUAffinity=0-2`.

### 3.4 Módulo de Notificación y Reportes (SMS)

`[RF-012]` **[Must Have]** Gestor de Mensajes SMS:
Envío de SMS a listado preconfigurado de usuarios autorizados mediante módulo GSM
gestionado por ModemManager (mmcli). Soporta dos modos:
- **Producción**: Ejecuta mmcli contra el módem Quectel EC25.
- **Desarrollo (DEV_MODE)**: Simula el envío mediante log, sin hardware real.

`[RF-013]` **[Must Have]** Reportes Programados:
Envío automático de resumen de turno en horarios configurables (por defecto 06:00, 14:00, 22:00).
Los reportes se generan mediante plantillas configurables por el administrador (ver RF-009).
El scheduler verifica cada 30 segundos si debe enviar reportes.

`[RF-014]` **[Must Have]** Alertas de Seguridad:
Notificación inmediata via SMS al administrador cuando un usuario acumule 3 o más intentos
fallidos de inicio de sesión consecutivos.

### 3.5 Módulo de Administración y Configuración

`[RF-015]` **[Must Have]** Configuración Dinámica de Puertos:
Interfaz Admin para modificar rutas hardware (RS485 báscula, RS232 PC, módem GSM),
baudrate, paridad, data bits, stop bits para cada puerto.

`[RF-016]` **[Should Have]** Prueba de Conectividad:
Función "Test" para verificar comunicación serial (RS485/RS232) y GSM antes de guardar
cambios. Endpoint `POST /api/config/test/{port}` donde port ∈ {rs485, rs232, gsm}.

`[RF-017]` **[Must Have]** Persistencia de Configuración:
Guardado en `config.yaml` con escritura atómica (archivo temporal + `os.replace`).
Aplicación automática de configuración tras reinicio del servicio. Sincronización de reloj.

### 3.6 Módulo de Gestión de Usuarios e Identidad

`[RF-021]` **[Must Have]** Administración de Usuarios (CRUD):
Interfaz Admin para Crear/Leer/Actualizar/Desactivar usuarios.
Campos: username, password (hasheada), full_name, document, role (admin/operator/corresponsal),
is_active, phone, failed_login_attempts. Desactivación lógica (is_active = false).
El modelo `User` incluye además: force_password_change (Boolean), reset_pin (String, hash),
reset_pin_expires_at (TIMESTAMP).

### 3.7 Módulo de Seguridad y Contingencia

`[RF-020]` **[Must Have]** Modo Manual de Emergencia:
Sistema completo de modo manual con dos orígenes de activación:

**Activación desde kiosco:**
- El analista solicita modo manual mediante un modal, seleccionando un supervisor (rol admin)
  de una lista e ingresando un motivo obligatorio.
- SIP-Edge envía un SMS al supervisor con datos del analista y motivo.
- El supervisor autoriza respondiendo: `manual on` (24h), `manual on Xh`, `manual on Xm`.
- Comando case-insensitive.

**Activación directa por SMS:**
- El supervisor envía `manual on [duración]` directamente sin solicitud previa.

**Comportamiento:**
- El campo de peso se vuelve editable mientras el modo manual esté activo.
- Extensiones: `manual on EXT Xh` / `manual on EXT Xm`.
- Suspensión: `manual off`.
- Expiración automática al alcanzar el tiempo autorizado.
- Múltiples solicitudes simultáneas permitidas (distintos admins). Gana la primera respuesta.
- Toda acción queda registrada en tabla `emergency_mode_log` para auditoría.
- El estado persiste ante cortes de energía (se recupera al reiniciar).

`[RF-030]` **[Must Have]** Restablecimiento Remoto de Contraseña vía SMS:
El administrador puede restablecer la contraseña de un analista de forma remota:

1. Admin envía SMS: `reset password <username>` (case-insensitive).
2. Sistema valida que el usuario existe y tiene teléfono registrado.
3. Genera un PIN numérico de 4 dígitos, lo hashea con bcrypt y lo almacena con
   expiración de 1 hora (single-use).
4. Envía el PIN por SMS al teléfono registrado del analista.
5. En el login, el enlace "Olvidó su contraseña" abre un modal con campos usuario + PIN.
6. Si el PIN es correcto y no ha expirado, se emite un reset_token JWT (5 min de validez).
7. Segundo modal permite ingresar nueva contraseña + confirmación.
8. Al completar, se actualiza password_hash, se limpian reset_pin/reset_pin_expires_at,
   y se desactiva force_password_change.
9. Si el usuario no tiene teléfono registrado, se envía SMS de error al admin.

### 3.8 Módulo de Respaldos

`[RF-018]` **[Must Have]** Rutina de Respaldo Automático:
Tarea diaria de volcado (`dump.sql.gz`) con rotación FIFO de 30 días.
El script de respaldo es ejecutado por el usuario de sistema `bkmngr` via cron.

`[RF-019]` **[Should Have]** Exportación a Medios Externos:
Copia de respaldos a USB/SD con verificación CRC32.

`[RF-023]` **[Must Have]** Tabla backup_logs:
Registro de cada ejecución de respaldo con: filename, file_size, local_checksum,
usb_copied, usb_checksum, error_message, created_at.

`[RF-024]` **[Must Have]** Endpoint GET /api/backup/status:
Retorna los últimos 10 registros de backup_logs. Solo accesible por admin.

`[RF-025]` **[Must Have]** Endpoint POST /api/backup/run:
Dispara un respaldo en background y retorna 202 Accepted. Solo accesible por admin.

---

## 4. Requisitos No Funcionales (RNF)

### 4.1 Rendimiento y Eficiencia
`[RNF-001]` Latencia de UI: Respuesta < 200ms en eventos de peso (medido desde pulsación botón hasta feedback visual).
`[RNF-009]` Latencia de inferencia LLM: < 5 segundos para tool_calls simples (promedio esperado en ARM64 con 3 cores).
`[RNF-010]` Ventana de anomalías: El cálculo Z-Score sobre 120 registros debe completarse en < 500ms.

### 4.2 Fiabilidad y Disponibilidad
`[RNF-002]` Operación Offline: Registro local garantizado sin internet ni señal GSM.
`[RNF-003]` Recuperación ante Fallos: Servicios gestionados por systemd con `Restart=always` y watchdog de 30s.
`[RNF-004]` Restricción Rígida de Entrada: Campo de peso *readonly* en UI. Solo modificable vía respuesta serial válida de báscula o modo manual de emergencia.
`[RNF-011]` Tolerancia a fallos del LLM: Si llama-server no responde, el sistema no debe bloquearse. Las anomalías se registran sin reporte narrativo.

### 4.3 Seguridad e Integridad de Datos
`[RNF-005]` Validación Estricta de Entradas: Protección XSS y validación de tipos en todos los endpoints.
`[RNF-006]` Prevención de Inyección SQL: Uso obligatorio de ORM parametrizado (SQLAlchemy).
`[RNF-007]` Prevención de Inyección de Prompt: El LLM recibe datos estructurados (tool calls con schemas Pydantic), nunca texto crudo del usuario para acciones críticas.
`[RNF-008]` Gestión Segura de Credenciales: Almacenamiento en variables de entorno con permisos 600.
`[RNF-012]` PIN de restablecimiento: Almacenado hasheado con bcrypt, nunca en texto plano. Single-use. Expiración a 1 hora.
`[RNF-013]` Reset token JWT: Duración máxima de 5 minutos. Válido solo para el endpoint de cambio de contraseña.

### 4.4 Disponibilidad del LLM
`[RNF-014]` CPU Pinning: llama-server limitado a cores 0-2 vía taskset. No debe interferir con backend (core 3).
`[RNF-015]` DEV_MODE: Si la variable de entorno `DEV_MODE` está definida como true/1/yes, el sistema omite toda E/S serial y conexión con llama-server, operando en modo simulación.

---

## 5. Arquitectura Lógica Implementada

| Capa | Tecnología | Notas |
|------|-----------|-------|
| **Hardware** | EdgeBox RPi-200 (8GB/32GB eMMC) | RS485 para báscula, RS232 para PC, mini PCIe para GSM |
| **Backend** | Python 3.13+ FastAPI | SQLAlchemy ORM, JWT auth, asyncio para scheduler SMS |
| **Base de Datos** | MariaDB 11.8.6 (localhost) | Motor InnoDB. Tablas: users, weighings, haciendas, suertes, backup_logs, emergency_mode_log, report_templates, anomaly_log |
| **Agente IA** | llama.cpp + Qwen 2.5 1.5B Q4_K_M | 3 cores dedicados (taskset). Puerta de enlace HTTP :8080 |
| **Frontend** | HTML5 + HTMX + WebSockets | Página login con modales de reset. Kiosco de pesaje. Panel admin. |
| **SMS** | ModemManager + mmcli | GSM entrante y saliente. Dispatcher compartido: emergency_mode, password_reset, consultas IA |

### Tablas de Base de Datos

| Tabla | Propósito | Creada en |
|-------|-----------|-----------|
| `users` | Usuarios del sistema con roles, teléfono, PIN de reset | Feature #2 |
| `haciendas` | Haciendas (fincas) | Feature #4 |
| `suertes` | Suertes/lotes vinculadas a haciendas | Feature #4 |
| `weighings` | Registros de pesaje con 3 pesos | Feature #6 |
| `backup_logs` | Trazabilidad de respaldos | Feature #10 |
| `emergency_mode_log` | Auditoría de modo manual de emergencia | Feature #9 |
| `report_templates` | Plantillas de reportes programados configurables | Feature #8 |
| `anomaly_log` | Historial de anomalías detectadas | Feature #8 |

---

## 6. Mapeo Features ↔ Requisitos

| Feature | RFs que cubre |
|---------|---------------|
| #1 system_config | RF-015, RF-016, RF-017 |
| #2 auth_rbac | RF-001, RF-002, RF-026 |
| #3 user_management | RF-021 |
| #4 farm_lot_crud | RF-006, RF-007, RF-008 |
| #5 scale_integration | RF-003 |
| #6 weighing_capture | RF-004, RF-005 |
| #7 sms_service | RF-012, RF-013, RF-014 |
| #8 ai_agent | RF-009, RF-010, RF-011, RF-027, RF-028, RF-029 |
| #9 emergency_mode | RF-020 (RF-020a a RF-020k) |
| #10 backup_system | RF-018, RF-019, RF-023, RF-024, RF-025 |
| #11 rs232_transmission | RF-022 |
| #12 password_reset_sms | RF-030 |

---

## 7. Análisis de Vacíos y Mecanismos de Trazabilidad

### 7.1 Vacíos de Información Detectados

Durante el desarrollo de las 12 features se identificaron los siguientes vacíos en la trazabilidad:

**V1 — ERS no reflejaba decisiones de diseño emergentes:**
Decisiones críticas tomadas durante la implementación (CPU pinning, RS485/RS232 split,
3 capas de anomalías, formato CSV fijo RS232) no estaban documentadas en el ERS original
ni se propagaron formalmente desde los SDD specs.

**V2 — Sin enlace bidireccional entre ERS y SDD specs:**
Los SDD specs en `harness/specs/` usan IDs propios (R1, R2...) sin referencia a los RF del ERS.
El ERS no lista qué features o specs implementan cada RF.

**V3 — Criterios de aceptación evolucionaron sin registro formal:**
Los `acceptance` en `feature_list.json` se actualizaban durante discusiones con el usuario,
pero no existía un registro de cambios con fecha, motivo y versión anterior.

**V4 — Documentación operativa dispersa:**
Configuraciones de hardware (taskset, parámetros de puerto, modelo de LLM) están en
múltiples documentos (Informes, docs/, environment.md) sin un índice centralizado.

**V5 — Sin registro de alternativas descartadas a nivel de requisitos:**
Las alternativas descartadas se documentaban en los SDD design.md (locales a cada feature)
pero no había un registro global de decisiones arquitectónicas.

### 7.2 Mecanismos Propuestos para Prevenir Pérdida de Información

**M1 — Tabla de trazabilidad ERS ↔ Features (implementado en este documento):**
Cada RF incluye referencia a la feature que lo implementa. Cada feature lista los RFs
que cubre. Esto permite navegación bidireccional.

**M2 — Change Log en ERS (propuesto para v2.0):**
Cada actualización del ERS DEBE incluir una sección "Cambios en esta versión" que registre:
- RF añadidos, modificados o eliminados.
- Fecha y motivo del cambio.
- Feature(s) afectadas.

**M3 — Design Decision Record (DDR) centralizado:**
Crear `harness/docs/decisions/` con un archivo por decisión significativa:
```
harness/docs/decisions/
├── 001-rs485-rs232-split.md
├── 002-cpu-pinning-taskset.md
├── 003-three-layer-anomaly-detection.md
├── 004-zscore-vs-moving-average.md
└── 005-shared-sms-dispatcher.md
```
Cada DDR incluye: contexto, alternativas, decisión, consecuencias.

**M4 — Hook de actualización del ERS en el flujo SDD:**
Modificar el flujo SDD para que el reviewer verifique si el SDD spec introduce cambios
en requisitos del ERS. Si es así, el release-manager DEBE actualizar el ERS antes de
marcar `done`.

**M5 — Enlace cruzado en SDD specs:**
Cada SDD requirements.md DEBE incluir un campo `Covers:` que liste los RF del ERS.
Ejemplo:
```markdown
# Requirements — rs232_transmission
> Feature: Transmisión de Datos a PC vía RS232
> Covers: RF-022
```

---

## 📎 Anexo F: Future Scope (Requisitos Diferidos)

| ID Original | Nombre | Razón de Diferimiento | Precondición |
|-------------|--------|-----------------------|--------------|
| RF-D01 | Integración Hikvision | Dependencia externa | SLA API > 99.5% |
| RF-D02 | Validación Biométrica | RAM compite con LLM | InsightFace + Qwen < 6.5GB |
| RF-D03 | Doble Factor | Dependiente de Hikvision + biometría | Reactivar RF-D01 y RF-D02 |
| RF-D04 | Bot Telegram | Requiere internet estable | Disponibilidad >95% |
| RF-D05 | Visión Artificial (NVMe) | Almacenamiento insuficiente | SSD NVMe M.2 2242 |

---

## ✅ Checklist de Cambios Aplicados en v1.3 (vs v1.2)

```markdown
[✅] Sección 2.5.2: Puerto serial dividido en RS485 (báscula) y RS232 (PC externo)
[✅] RF-003: Especificado puerto RS485 para báscula DINI ARGEO DFWLI-2
[✅] RF-022: Nuevo — Transmisión de datos a PC vía RS232 con formato CSV fijo
[✅] RF-023/024/025: Nuevos — backup_logs, GET /api/backup/status, POST /api/backup/run
[✅] RF-026: Nuevo — Bloqueo por inactividad (feature #2)
[✅] RF-027: Nuevo — Catálogo de 12 herramientas SQL parametrizadas (feature #8)
[✅] RF-028: Nuevo — Invocación del LLM ante anomalía detectada (feature #8)
[✅] RF-029: Nuevo — CPU Pinning con taskset para llama-server (feature #8)
[✅] RF-030: Nuevo — Restablecimiento remoto de contraseña vía SMS (feature #12)
[✅] RF-009: Ampliado — De orquestador genérico a sistema completo de reportería configurable
[✅] RF-010: Ampliado — De Z-score simple a 3 capas de detección (Z-score, ratios, temporal)
[✅] RF-011: Ampliado — De consultas SQL estructuradas a Function Calling con 12 herramientas
[✅] RF-013: Ampliado — Reportes programados ahora con plantillas configurables por el admin
[✅] RF-020: Ampliado — De comando SMS simple a flujo completo con solicitud kiosco + aprobación supervisor + extensiones
[✅] Sección 2.2: Añadido rol Supervisor. Actualizado rol Analista con capacidades de solicitud de emergencia
[✅] Sección 6: Nuevo mapeo bidireccional features ↔ requisitos
[✅] Sección 7: Nuevo análisis de vacíos de información y mecanismos de trazabilidad
[✅] RNF-009 a RNF-015: Nuevos — Latencia LLM, tolerancia a fallos, PIN/reset token, CPU pinning, DEV_MODE
[✅] Tabla de BD: Actualizada con report_templates y anomaly_log
```

---

*Documento generado a partir del análisis completo del desarrollo de 12 features SDD,
los spec requirements, los closure reports y el código fuente implementado.*
