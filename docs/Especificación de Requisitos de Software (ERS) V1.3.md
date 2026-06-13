# Especificación de Requisitos de Software (ERS) – Versión 1.3
*Proyecto: Sistema Inteligente de Pesaje y Control de Materia Extraña (SIP-Edge)*  
*Plataforma: EdgeBox RPi-200 (8GB RAM / 32GB eMMC), Raspberry Pi OS x64*  
*Fecha: 13-Jun-2026*
*Cambios v1.3: Interfaces de hardware — RS485 para báscula + RS232 para PC externo*

---

## 1. Introducción

### 1.1 Propósito
El propósito de este documento es definir los requisitos funcionales y no funcionales para el desarrollo del **Sistema Inteligente de Pesaje y Control de Materia Extraña (SIP-Edge)**. Este sistema integrará lectura de hardware industrial (básculas) y un Agente de Inteligencia Artificial (TinyLLM) para la detección de anomalías y reportes automatizados vía SMS.

> ✅ **Corrección aplicada**: Eliminada referencia a *"biometría facial local"* (funcionalidad diferida a Future Scope - Anexo F).

### 1.2 Alcance
El sistema funcionará como una solución *standalone* (autónoma) desplegada en el laboratorio de cañas. Gestionará:

- Captura y almacenamiento de registros de peso (caña y materia extraña) con autenticación por credenciales.
- Análisis de datos mediante Agente IA para detección de anomalías estadísticas.
- Notificaciones automatizadas vía SMS (reportes programados y alertas de seguridad).
- Gestión de usuarios con Control de Acceso Basado en Roles (RBAC).

> ✅ **Corrección aplicada**: Ampliado alcance para incluir explícitamente gestión de usuarios/RBAC (presente en RF-002 pero ausente en descripción original).

### 1.3 Contexto y Justificación de la Solución

#### 1.3.1 Situación Actual
Actualmente, el laboratorio de cañas opera como una *"isla de información"* dentro de la planta, con reportes de materia extraña vía email o comunicación verbal bajo demanda, y registro de datos fuera de línea. El sistema Legacy presenta:

- Brechas de seguridad en validación de identidad durante el registro de pesos.
- Pérdida de información por borrado accidental de base de datos.
- Detección manual y reactiva de anomalías de peso, dependiendo enteramente de la pericia del operador.

#### 1.3.2 Valor Aportado por la Solución
La implementación del SIP-Edge aporta valor estratégico en tres ejes:

- **Integridad Operativa**: Autenticación robusta por credenciales + RBAC garantiza trazabilidad de quién realizó cada transacción.
- **Inteligencia en el Borde (Edge AI)**: El Agente IA audita cada peso en tiempo real detectando anomalías estadísticas instantáneamente, reduciendo pérdidas por errores humanos.
- **Conectividad Resiliente**: Notificaciones SMS vía módulo GSM garantizan supervisión remota sin dependencia de infraestructura de red corporativa.

> ✅ **Corrección aplicada**: Eliminado *"Doble Factor Implícito"* (requería Hikvision/biometría, funcionalidades diferidas). Reemplazado por *"Autenticación robusta por credenciales + RBAC"*.

### 1.4 Definiciones, Acrónimos y Abreviaturas

| Término | Definición |
|---------|------------|
| **SIP-Edge** | Sistema Inteligente de Pesaje y Control de Materia Extraña |
| **TinyLLM** | Modelo de Lenguaje Pequeño (SLM) optimizado para dispositivos edge (ej: Qwen 2.5 3B) |
| **RBAC** | Role-Based Access Control (Control de Acceso Basado en Roles) |
| **RAG** | *No aplicable en v1.0*: Retrieval-Augmented Generation requiere vector DB (no presente). En su lugar: *"Análisis SQL con Function Calling"* |
| **GSM** | Global System for Mobile Communications (módulo de comunicación celular) |
| **eMMC** | Embedded MultiMediaCard (almacenamiento integrado de 32GB) |
| **RF** | Requisito Funcional |
| **RNF** | Requisito No Funcional |
| **D-XXX** | Dependencia externa crítica |
| **S-XXX** | Suposición de entorno |

> ✅ **Mejora aplicada**: Sección nueva según estándar IEEE 29148 para evitar ambigüedades.

### 1.5 Referencias
- Manual de Protocolo de Comunicación de Báscula (pendiente entrega fabricante) – `[D-001]`
- Especificación Técnica Qwen 2.5 3B (GGUF) – Alibaba Group
- Documento de Evaluación y Selección de TinyLLM (SLM) – Anexo Interno

---

## 2. Descripción General

### 2.1 Perspectiva del Proyecto
El sistema opera en la capa de *Edge Computing*. Interactúa con tres actores principales:

- **Hardware de Proceso**: Báscula conectada vía RS485 (comando-respuesta) y PC externo conectado vía RS232 (envío de tramas de datos).
- **Hardware de Comunicación**: Módulo GSM + SIM (mini PCIe), solo para envío de SMS (sin acceso entrante desde internet).
- **Usuarios**: Operador (presencial), Corresponsal/Gerente (remoto vía SMS), Administrador (configuración).

> ✅ **Corrección aplicada**: Eliminado *"Hardware de Perímetro (Hikvision)"* (funcionalidad diferida).

### 2.2 Características de los Usuarios
- **Operador de Laboratorio**: Autenticación por credenciales (usuario/contraseña). Interacción mínima y ágil en kiosco.
- **Corresponsal/Gerente**: Recibe reportes gerenciales y alertas vía SMS (no interactúa con sistema).
- **Administrador**: Acceso total a configuración, gestión de usuarios y copias de seguridad. Autenticación por credenciales.

> ✅ **Corrección aplicada**: Eliminada referencia a *"biometría pasiva"* (S-001 eliminado – ver sección 2.4).

### 2.3 Restricciones Generales
- **Hardware**: EdgeBox RPi-200 (8GB RAM, 32GB eMMC, CPU ARM Cortex-A72).
- **Respaldo Eléctrico**: Power bank en línea (10.000–25.000 mAh).
- **Conectividad**: Operatividad 100% offline garantizada (solo SMS requiere señal GSM).
- **Ambiente**: Industrial (polvo, vibración, iluminación variable). *No se requiere iluminación controlada para procesamiento biométrico (biometría diferida).*

> ✅ **Corrección aplicada**: Eliminada suposición de iluminación para biometría (S-001 eliminado).

### 2.4 Suposiciones y Dependencias
- `[D-001]` **Protocolo de Báscula**: Se asume que la báscula dispone de puerto serial (RS232/USB) con protocolo ASCII estándar y manual de comunicación accesible.
- `[D-002]` **Cobertura GSM**: El envío de SMS depende de señal celular 3G/4G estable en la ubicación del laboratorio (>85% uptime esperado).

> ✅ **Corrección aplicada**: Eliminado `[D-002]` original (API Hikvision) y `[S-001]` (iluminación para biometría), ambos no aplicables en v1.0.

### 2.5 Requisitos de Interfaz Externa

#### 2.5.1 Interfaces de Usuario (UI)
- **Estilo Kiosco**: Diseñada para pantallas ≥13" con teclado y mouse.
- **Feedback Visual**: Códigos de color universales (Verde=Éxito, Rojo=Error, Amarillo=Procesando).

#### 2.5.2 Interfaces de Hardware
| Puerto/Socket | Asignación | Notas |
|---------------|------------|-------|
| USB 1 | Mouse y teclado | Único puerto USB requerido en v1.0 |
| Serial RS485 | Báscula | Comunicación comando-respuesta |
| Serial RS232 | PC Externo | Envío de tramas de información |
| mini PCIe | Módulo GSM/LTE | Solo envío de SMS |
| M.2 | *Sin asignar* | Reservado para NVMe en Future Scope (Anexo F) |

> ✅ **Corrección aplicada**: Eliminado puerto USB para webcam (no requerido en v1.0). M.2 marcado como reservado para futuro.
> ✅ **Cambio v1.3**: Puerto serial dividido en RS485 (báscula) y RS232 (PC externo).

#### 2.5.3 Interfaces de Software
- **Sistema Operativo**: Raspberry Pi OS (64-bit) Bullseye o superior.
- **Base de Datos**: MariaDB 10.5+ (motor InnoDB).
- **Runtime**: Python 3.10+.

---

## 3. Requisitos Funcionales (RF)

### 3.1 Módulo de Autenticación y Seguridad
`[RF-001]` **[Must Have]** Autenticación por Credenciales: El sistema validará identidad mediante usuario/contraseña con hash seguro (bcrypt).
`[RF-002]` **[Must Have]** Control de Acceso Basado en Roles (RBAC): Restricción de funcionalidades según rol:
- *Operador*: Solo formulario de pesaje y sus registros del turno actual.
- *Corresponsal*: Recepción de reportes/alertas vía SMS (sin acceso al sistema).
- *Administrador*: Acceso total (configuración, gestión de usuarios, respaldos).

### 3.2 Módulo de Pesaje y Datos
`[RF-003]` **[Must Have]** Interacción Bidireccional con Báscula (Comando-Respuesta vía RS485): Protocolo activo donde el sistema:
- Envía comando específico (string/hex) al puerto RS485 al presionar botones de control (Tara Total, Peso Mineral, etc.).
- Espera respuesta con timeout configurable (500ms–3000ms, valor por defecto: 1500ms).
`[RF-004]` **[Must Have]** Persistencia de Datos: Almacenamiento en MariaDB de (Peso, ID Usuario, Fecha, Hora, Tipo de Material, Hacienda, Suerte).
`[RF-005]` **[Must Have]** Integridad Transaccional: Registro de peso y metadata como transacción atómica única (commit/rollback).
`[RF-006]` **[Must Have]** Gestión de Haciendas: Interfaz Admin para Crear/Editar/Desactivar (borrado lógico). Sin eliminación física si existen registros asociados.
`[RF-007]` **[Must Have]** Gestión de Suertes/Lotes: Gestión obligatoriamente vinculada a Hacienda padre.
`[RF-008]` **[Must Have]** Selección en Cascada: Carga dinámica de Suertes según Hacienda seleccionada.
`[RF-022]` **[Must Have]** Transmisión de Datos a PC vía RS232: El sistema DEBE enviar tramas de información estructurada a un PC externo a través del puerto RS232 configurado. La trama contendrá datos relevantes del registro de pesaje actual (Peso, Fecha, Hora, Tipo de Material, Hacienda, Suerte) en formato configurable (ASCII/CSV/JSON). La transmisión se dispara automáticamente tras cada registro exitoso.

> ✅ **Cambio v1.3**: Añadido RF-022 para transmisión RS232 a PC externo.

### 3.3 Agente de Orquestación y Análisis (TinyLLM Agent)
`[RF-009]` **[Must Have]** Orquestador de Consultas (AI Agent): Agente basado en Qwen 2.5 3B (GGUF) con capacidad de *Function Calling* para ejecutar herramientas predefinidas en Python.
`[RF-010]` **[Must Have]** Detección Proactiva de Anomalías: Análisis estadístico sobre últimos 120 registros o últimas 4 horas (lo que ocurra primero) para identificar desviaciones (Z-score > 3).
`[RF-011]` **[Should Have]** Análisis SQL Estructurado con Function Calling: El Agente resolverá consultas cuantitativas invocando herramientas SQL parametrizadas, evitando alucinación de datos numéricos.

> ✅ **Corrección aplicada**: 
> - Reformulado RF-011: Eliminado término *"RAG"* (requiere vector DB, no presente). Reemplazado por *"Análisis SQL con Function Calling"*.
> - Especificado umbral estadístico (Z-score > 3) y ventana de análisis (120 registros / 4 horas).

### 3.4 Módulo de Notificación y Reportes (SMS)
`[RF-012]` **[Must Have]** Gestor de Mensajes SMS: Envío a listado preconfigurado de usuarios autorizados mediante módulo GSM (comandos AT).
`[RF-013]` **[Must Have]** Reportes Programados: Envío automático de resumen de turno (06:00, 14:00, 22:00) y horarios configurables por Admin.
`[RF-014]` **[Must Have]** Alertas de Seguridad: Notificación inmediata de intentos de operación por usuarios con rol no autorizado o sesión expirada.

> ✅ **Corrección aplicada**: 
> - Eliminado bullet point inconsistente (`• [RF-013]` → `[RF-012]` con numeración secuencial).
> - Reformulado RF-014: Eliminado *"usuarios no presentes en perímetro"* (concepto no implementable sin Hikvision). Reemplazado por *"usuarios con rol no autorizado o sesión expirada"*.

### 3.5 Módulo de Administración y Configuración
`[RF-015]` **[Must Have]** Configuración Dinámica de Puertos: Interfaz gráfica Admin para modificar rutas hardware (Báscula RS485, PC RS232, Módem GSM), baudrate, paridad.
`[RF-016]` **[Should Have]** Prueba de Conectividad: Función "Test" para verificar comunicación serial/GSM antes de guardar cambios.
`[RF-017]` **[Must Have]** Persistencia de Configuración: Guardado en `config.yaml`, aplicación automática tras reinicio y sincronización de reloj.
`[RF-018]` **[Must Have]** Rutina de Respaldo Automático: Tarea diaria de volcado (`dump.sql.gz`) con rotación FIFO de 30 días (elimina más antiguo al día 31).
`[RF-019]` **[Should Have]** Exportación a Medios Externos: Copia de respaldos a USB/SD con verificación CRC32.
`[RF-020]` **[Must Have]** Modo Manual de Emergencia: Activable por Admin mediante comando SMS predefinido (`MANUAL_ON`). Desactiva bloqueo de hardware (RNF-006) temporalmente (máx. 15 minutos).

> ✅ **Corrección aplicada**: 
> - Insertado RF-020 para modo manual (vinculado a RNF-006, ausente en v1.1 original).
> - Especificado timeout de modo manual (15 minutos) para mitigar riesgo de operación no auditada.

### 3.6 Módulo de Gestión de Usuarios e Identidad
`[RF-021]` **[Must Have]** Administración de Usuarios (CRUD): Interfaz gráfica Admin para Crear/Leer/Actualizar/Desactivar usuarios (Nombre, Documento, Rol, Estado).

> ✅ **Corrección aplicada**: Numeración secuencial corregida (RF-021 reinsertado). Eliminado salto RF-020→RF-022 original.

---

## 4. Requisitos No Funcionales (RNF)

### 4.1 Rendimiento y Eficiencia
`[RNF-001]` Latencia de UI: Respuesta < 200ms en eventos de peso (medido desde pulsación botón hasta feedback visual).

### 4.2 Fiabilidad y Disponibilidad
`[RNF-002]` Operación Offline: Registro local garantizado sin internet ni señal GSM (solo afecta envío de SMS).
`[RNF-003]` Recuperación ante Fallos: Servicios críticos gestionados por systemd con `Restart=always` y watchdog de 30s.
`[RNF-004]` Restricción Rígida de Entrada: Campo de peso *readonly* en UI. Solo modificable mediante respuesta serial válida de báscula.
- *Contingencia*: Modo manual activable exclusivamente por Admin vía SMS (`MANUAL_ON`, RF-020).

### 4.3 Seguridad e Integridad de Datos
`[RNF-005]` Validación Estricta de Entradas: Protección XSS y validación de tipos en todos los endpoints.
`[RNF-006]` Prevención de Inyección SQL: Uso obligatorio de ORM parametrizado (SQLAlchemy).
`[RNF-007]` Prevención de Inyección de Prompt: Texto crudo nunca pasado al Agente IA para acciones críticas (solo tool calls con schemas Pydantic validados).
`[RNF-008]` Gestión Segura de Credenciales: Almacenamiento en variables de entorno (`/etc/environment`) con permisos 600.

> ✅ **Corrección aplicada**: Numeración RNF corregida (RNF-001 a RNF-008 secuencial, eliminados RNF-002/RNF-003 originales no aplicables sin biometría).

---

## 5. Arquitectura Lógica Propuesta

| Capa | Tecnología Seleccionada | Justificación |
|------|-------------------------|---------------|
| **Hardware** | EdgeBox RPi-200 (8GB/32GB eMMC) | Plataforma validada para edge computing industrial. *Nota: Socket M.2 reservado para NVMe en Future Scope (Anexo F)*. |
| **Backend** | Python 3.11 + FastAPI (Async) | Manejo concurrente de I/O serial/GSM sin bloqueos mediante `asyncio`. |
| **Base de Datos** | MariaDB (InnoDB) | Transacciones ACID para integridad de registros críticos de peso. |
| **Agente IA** | Llama.cpp + Qwen 2.5 3B (GGUF Q4_0) | Ejecución eficiente en ARM64 (<2.2GB RAM) con soporte nativo para Function Calling. |
| **Frontend** | HTML5 + HTMX + WebSockets | Interfaz ligera (<50MB RAM navegador) con actualizaciones parciales en tiempo real. |

> ✅ **Corrección aplicada**: Eliminada referencia a *"Cámara Estéreo si se activa RF-D01"*. Reemplazado por nota sobre socket M.2 reservado para Future Scope.

---

## 📎 Anexo F: Future Scope (Requisitos Diferidos)

*Este anexo documenta funcionalidades técnicamente viables excluidas del alcance de la Versión 1.0 (MVP) para reducir complejidad inicial y garantizar estabilidad operativa en hardware limitado (8GB RAM).*

### F.1 Matriz de Requisitos Diferidos

| ID Original | Nombre | Razón de Diferimiento | Precondición para Reactivación |
|-------------|--------|------------------------|--------------------------------|
| RF-001 (v1.0) | Integración Hikvision DS-K1T343 | Dependencia externa no controlable (API ISAPI). Riesgo operativo si falla. | SLA API > 99.5% + latencia < 500ms en LAN |
| RF-002 (v1.0) | Validación Biométrica Local (InsightFace) | Consumo RAM >1.2GB compite con TinyLLM (Qwen 2.5 3B ~2.2GB). Total excedería 8GB. | Benchmark validado: InsightFace + Qwen < 6.5GB RAM total |
| RF-003 (v1.0) | Lógica de Doble Factor Implícito | Dependiente de Hikvision + biometría (ambos diferidos). | Reactivación previa de RF-001 y RF-002 v1.0 |
| RF-014 (v1.0) | Bot Interactivo Telegram | Requiere internet estable. SMS garantiza operatividad 100% offline. | Disponibilidad internet >95% uptime en sitio |
| RF-023/024 (v1.0) | Enrolamiento Biométrico + Vinculación Telegram | Sin biometría ni Telegram activos, funcionalidades innecesarias. | Reactivación de RF-002 y RF-014 v1.0 |
| RF-D01 (v1.0) | Dataset para Visión Artificial (Cámara Estéreo) | Requiere almacenamiento NVMe >512GB (no disponible en 32GB eMMC). | Instalación SSD NVMe M.2 2242 + caso de uso validado |

### F.2 Roadmap Técnico Propuesto

| Fase | Versión | Timeline Esperado | Capabilities Prioritarias |
|------|---------|-------------------|---------------------------|
| **MVP** | 1.0 | Corriente | • Autenticación por credenciales<br>• Pesaje serial comando-respuesta<br>• Agente IA para anomalías<br>• Notificaciones SMS |
| **Expansión** | 2.0 | +6 meses post-MVP | • Biometría facial ligera (1:1)<br>• Telegram + SMS híbrido<br>• Monitoreo de batería vía GPIO |
| **Optimización** | 3.0 | +12 meses post-MVP | • Integración Hikvision (lectura asíncrona)<br>• Dataset para visión artificial |

### F.3 Criterios Objetivos para Reactivación
Una funcionalidad diferida podrá reactivarse **solo cuando TODAS** estas condiciones se cumplan:
1. ✅ MVP operando con disponibilidad >98% durante 30 días consecutivos.
2. ✅ Consumo RAM pico sistema base <5.5GB (dejando 2GB para expansión).
3. ✅ Caso de negocio cuantificado (ej: reducción de fraude >5% con biometría).
4. ✅ Presupuesto aprobado para hardware adicional (si aplica).

> ℹ️ **Referencia Estándar**: IEEE/ISO/IEC/IEEE 29148:2018 (Sección 5.3.7 – *"Out of Scope Requirements"*).

---

## ✅ Checklist de Cambios Aplicados en v1.2

```markdown
[✅] Eliminadas todas las referencias a biometría facial en secciones 1.1, 1.2, 1.3.2
[✅] Corregida numeración RF secuencial (RF-008 y RF-021 reinsertados)
[✅] Reformulado RF-014: eliminado "perímetro", reemplazado por "rol no autorizado/sesión expirada"
[✅] Eliminado S-001 (iluminación para biometría) – no aplicable en v1.0
[✅] Insertado RF-020: modo manual de emergencia (vinculado a RNF-004)
[✅] Reformulado RF-011: eliminado "RAG", especificado "SQL con Function Calling"
[✅] Actualizada tabla de arquitectura: referencia a M.2 como reservado para Future Scope
[✅] Agregadas secciones 1.4 (Definiciones) y 1.5 (Referencias)
[✅] Incluido Anexo F: Future Scope con matriz de requisitos diferidos y roadmap
[✅] Corregida numeración RNF (secuencial RNF-001 a RNF-008)
```
 
Este documento **ERS v1.3** está listo para servir como base del Software Design Document (SDD).

---

## ✅ Checklist de Cambios Aplicados en v1.3

```markdown
[✅] Sección 2.1: Hardware de Proceso actualizado a RS485 + RS232
[✅] Sección 2.5.2: Tabla de interfaces con RS485 (báscula) y RS232 (PC)
[✅] Sección 3.2 RF-003: Especificado puerto RS485 para báscula
[✅] Sección 3.2 RF-022: Nuevo requisito para transmisión RS232 a PC
[✅] Sección 3.5 RF-015: Configuración dinámica ampliada a RS485 + RS232 + GSM
```