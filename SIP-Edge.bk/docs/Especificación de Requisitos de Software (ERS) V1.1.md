***

# Especificación de Requisitos de Software (ERS)
**Proyecto:** Sistema Inteligente de Pesaje y Control de Materia Extraña (SIP-Edge)

**Versión:** 1.1

**Plataforma:** EdgeBox RPi-200 (8GB RAM / 32GB eMMC), Raspberry Pi OS x64

**Documentos de Referencia:** Auditoria de software Legacy

**Documentos Anexos:** Evaluación y Selección de TinyLLM (SLM)

---

## 1. Introducción

### 1.1 Propósito
El propósito de este documento es definir los requisitos funcionales y no funcionales para el desarrollo del "Sistema Inteligente de Pesaje y Control de Materia Extraña". Este sistema integrará biometría facial local, lectura de hardware industrial (básculas) y un Agente de Inteligencia Artificial (TinyLLM) para la detección de anomalías y reportes automatizados vía Telegram.

### 1.2 Alcance
El sistema funcionará como una solución *standalone* (autónoma) desplegada en el laboratorio de cañas. Gestionará:
1.  Captura y almacenamiento de registros de peso (caña y materia extraña).
2.  Análisis de datos mediante Agente IA para detección de anomalías.


### 1.3 Contexto y Justificación de la solución
### 1.3.1 Situación Actual
- Actualmente, el laboratorio de cañas opera como una "isla de información" dentro de la planta. Con reportes de materia extraña via email o voz a voz bajo demanda, con registro de datos fuera de linea.
- El sistema de software Legacy actual presenta limitaciones en la validación de identidad, lo que abre una brecha de seguridad durante el registro de pesos de caña y materia extraña, perdida de informacion por borrado de base de datos. Adicionalmente, la detección de errores en los datos (anomalías de peso) es un proceso manual y reactivo, que depende enteramente de la pericia del operador o de auditorías posteriores, lo que retrasa la toma de decisiones gerenciales.
### 1.3.2 Valor Aportado por la Solución
La implementación del sistema SIP-Edge aporta valor estratégico en tres ejes fundamentales:
- Inteligencia en el Borde (Edge AI): La incorporación de un Agente de IA permite pasar de un registro pasivo a un monitoreo proactivo. El sistema audita cada peso en tiempo real (in-situ) detectando anomalías estadísticas instantáneamente, reduciendo pérdidas por errores humanos o fraude.
- Conectividad y Visibilidad: A través de la integración con mensajeria SMS, se rompe el aislamiento del laboratorio, permitiendo que los gerentes y corresponsales reciban reportes de turno y alertas de seguridad en sus dispositivos móviles (programados, por deteccion de anomalias o bajo demanda), facilitando una supervisión remota instantanea y efectiva sin depender de la infraestructura de red corporativa (gracias al respaldo GSM).

---

## 2. Descripción General

### 2.1 Perspectiva del Proyecto
El sistema opera en la capa de *Edge Computing*. Interactúa con cuatro actores principales:
*   **Hardware de Proceso:** Báscula Serial (Conectada al EdgeBox).
*   **Hardware de Comunicación:** Módulo GSM + SIM, solo para envío de mensajes (sin acceso desde internet).
*   **Usuarios Remotos:** Corresponsales y Gerentes vía SMS.

### 2.2 Características de los Usuarios
*   **Operador de Laboratorio:** Usuario presencial. Requiere interacción mínima y ágil. Autenticación por contraseña.
*   **Corresponsal/Gerente:** Usuario remoto. recibe reportes gerenciales via SMS.
*   **Administrador:** Acceso a configuración del sistema y gestión de usuarios. Autenticación por contraseña.

### 2.3 Restricciones Generales
*   **Hardware:** Limitado a EdgeBox RPi-200 con 8 GB de RAM, almacenamiento eMMC de 32GB y CPU ARM Cortex-A72.
*   **Respaldo Eléctrico:** Power bank en línea entre 10.000 y 25.000 mAh - dependiendo de la configuracion final del hardware.
*   **Conectividad:** Debe tolerar intermitencia de internet, manteniendo la operatividad local (MariaDB).
*   **Ambiente:** Entorno industrial (polvo, vibración, iluminación variable).

### 2.4 Suposiciones y Dependencias
*	**[D-001] Protocolo de Báscula:** Se asume que la báscula a conectar dispone de un puerto de comunicación serial (RS232/USB) y que el fabricante provee el manual del protocolo de comunicación (trama de datos) accesible y estándar (ASCII).
*	**[D-002] Cobertura GSM:** El envío de mensajes SMS depende de la disponibilidad de señal celular 3G/4G en la ubicación física del laboratorio.
*	**[S-001] Iluminación:** Se asume que el puesto de pesaje cuenta con iluminación artificial adecuada y constante para permitir que la webcam USB capture imágenes claras para el reconocimiento facial. El software no podrá compensar condiciones de oscuridad total.

### 2.5 Requisitos de Interfaz Externa
### 2.5.1 Interfaces de Usuario (UI)
*	**Estilo Kiosco:** La interfaz gráfica está diseñada para pantallas de 13" o mas. Con disponibilidad de teclado y mouse.
Feedback Visual: El sistema utilizará códigos de color universales (Verde=Éxito, Rojo=Error/Alerta, Amarillo=Procesando) en pantalla para indicar el estado de las transacciones sin obligar al operador a leer textos largos.
### 2.5.2 Interfaces de Hardware
- Puerto USB 1 : Reservado para mouse y teclado.
- Puerto Serial: Reservado para adaptador RS232-USB de la Báscula.
- Socket mini PCIe:  Reservado para interfaz GSM/LTE.
### 2.5.3 Interfaces de Software
Sistema Operativo: El sistema se desplegará sobre Raspberry Pi OS (64-bit) Bullseye o superior.
Motor de Base de Datos: MariaDB 10.5+.
Python: Version 3.10 o superior


---
## 3. Requisitos Funcionales (RF)

### 3.1 Módulo de Autenticación y Seguridad (Biometría Híbrida)

*   **[RF-001] [Prioridad: Must Have] autenticacion por credenciales:** El sistema deberá utilizar un sistema de autenticacion via credenciales (usuario/contraseña) para verificar la identidad del operador.
*   **[RF-002] [Prioridad: Must Have] Control de Acceso Basado en Roles (RBAC):** El sistema deberá restringir el acceso a las funcionalidades según el rol asignado al usuario autenticado:
    *   *Operador:* Acceso exclusivo al formulario de pesaje y visualización de sus propios registros del turno actual.
    *   *Corresponsal:* Autorización para recibir tanto reportes históricos, como alertas de anomalíasvía SMS.
    *   *Administrador:* Acceso total, incluyendo configuración de hardware, gestión de usuarios y copias de seguridad.

### 3.2 Módulo de Pesaje y Datos

*   **[RF-003] [Prioridad: Must Have] Interacción Bidireccional con Báscula (Comando-Respuesta):** El sistema deberá gestionar la comunicación con la báscula mediante un protocolo activo de solicitud y respuesta, eliminando la lectura pasiva de flujos continuos.
    *   *Acción:* Al accionar los botones de control en la interfaz (Tara Total, Tara Mineral, Tara Vegetal, Peso Total, Peso Mineral, Peso Vegetal), el sistema enviará la cadena de comando específica (string/hex) al puerto serial.
    *   *Captura:* El sistema esperará durante un tiempo definido (timeout) la trama de respuesta enviada por la báscula para confirmar la ejecución exitosa o capturar el valor numérico.
*   **[RF-004] [Prioridad: Must Have] Persistencia de Datos:** Todos los registros (Peso, ID Usuario, Fecha, Hora, Tipo de Material) deberán almacenarse en una base de datos relacional local (MariaDB).
*   **[RF-005] [Prioridad: Must Have] Integridad Transaccional:** El registro de peso y la evidencia de identidad deben guardarse como una transacción atómica única.
*   **[RF-006] [Prioridad: Must Have] Gestión de Haciendas:** El sistema dispondrá de una interfaz (accesible para Administradores) para gestionar el catálogo de Haciendas.
    *   *Funcionalidad:* Crear, Editar y Desactivar (Borrado Lógico).
    *   *Restricción:* No se permitirá eliminación física si existen registros históricos asociados.
*   **[RF-007] [Prioridad: Must Have] Gestión de Suertes/Lotes:** Gestión de "Suertes" obligatoriamente vinculadas a una Hacienda padre.
*   **[RF-009] [Prioridad: Must Have] Selección en Cascada:** La selección de "Suerte" en el formulario se cargará dinámicamente según la "Hacienda" seleccionada.

### 3.3 Agente de Orquestación y Análisis (TinyLLM Agent)

*   **[RF-010] [Prioridad: Must Have] Orquestador de Consultas (AI Agent):** El módulo operará como un Agente de IA basado en el modelo **Qwen 2.5 (3B)**. Este agente tendrá la capacidad de razonamiento para transformar solicitudes en lenguaje natural en la ejecución de **herramientas de software** (Function Calling) predefinidas en Python, garantizando un acceso seguro a los datos.
*   **[RF-011] [Prioridad: Must Have] Detección Proactiva de Anomalías:** El Agente deberá, bajo demanda o trigger automático, utilizar herramientas de análisis estadístico sobre los últimos registros (N=100-150) para identificar desviaciones y generar alertas descriptivas.
*   **[RF-012] [Prioridad: Should Have] Análisis RAG Estructurado (SQL-Based):** El Agente resolverá consultas cuantitativas invocando herramientas de consulta SQL seguras, evitando la alucinación de datos numéricos y garantizando la congruencia con la base de datos.

### 3.4 Módulo de Notificación y Reportes (SMS)

•	**[RF-013] [Prioridad: Must Have] Gestor de mensajes SMS**: envio de mensajes a traves de SMS a listado de usuarios autorizados.
*   **[RF-014] [Prioridad: Must Have] Reportes Programados:** Envío automático de resumen de turno (06:00, 14:00, 22:00) y horarios configurables.
*   **[RF-015] [Prioridad: Must Have] Alertas de Seguridad:** Notificación inmediata de intentos de operación por usuarios no presentes en perímetro.

### 3.5 Módulo de Administración y Configuración

*   **[RF-016] [Prioridad: Must Have] Configuración Dinámica de Puertos:** Interfaz gráfica para Admin que permite modificar rutas de hardware (Báscula, Módem), Baudrate, Paridad, etc.
*   **[RF-017] [Prioridad: Should Have] Prueba de Conectividad:** Función de "Test" para verificar comunicación con puertos antes de guardar cambios.
*   **[RF-018] [Prioridad: Must Have] Persistencia de Configuración:** Guardado local (config.yaml/.env), aplicación y sincronizacion de reloj automática tras reinicio.
*   **[RF-019] [Prioridad: Must Have] Rutina de Respaldo Automático:** Tarea programada diaria para volcado (dump .sql.gz) de MariaDB con rotación de 30 días.
*   **[RF-020] [Prioridad: Should Have] Exportación a Medios Externos:** Funcionalidad para copiar respaldos a USB/SD con verificación de integridad.


### 3.6 Módulo de Gestión de Usuarios e Identidad

*   **[RF-022] [Prioridad: Must Have] Administración de Usuarios (CRUD):** El sistema dispondrá de una interfaz gráfica (Admin) para Crear, Leer, Actualizar y Desactivar usuarios.
    *   *Datos:* Nombre, Documento, Rol, Estado.

---

## 4. Requisitos No Funcionales (RNF)

### 4.1 Rendimiento y Eficiencia
*   **[RNF-001] Latencia de UI:** Respuesta < 200ms en eventos de peso.

### 4.2 Fiabilidad y Disponibilidad
*   **[RNF-004] Operación Offline:** Registro local garantizado sin internet.
*   **[RNF-005] Recuperación ante Fallos:** Systemd `restart=always` para servicios críticos (incluye reloj de tiempo real).
*   **[RNF-006] Restricción Rígida de Entrada (Candado de Hardware):** Campo de peso *readonly* en operación normal. Solo se pueden escribir los campos de peso a traves respuesta serial válida por parte de la balanza.
    *   *Contingencia:* Modo manual activable por Admin vía SMS.

### 4.3 Seguridad e Integridad de Datos
*   **[RNF-007] Validación Estricta de Entradas:** Protección contra XSS y validación de tipos.
*   **[RNF-008] Prevención de Inyección SQL:** Uso obligatorio de ORM.
*   **[RNF-009] Prevención de Inyección de Prompt:** No pasar texto crudo al Agente IA para acciones críticas.
*   **[RNF-010] Gestión Segura de Credenciales:** Uso de variables de entorno.

---

## 5. Arquitectura Lógica Propuesta

| Capa | Tecnología Seleccionada | Justificación |
| :--- | :--- | :--- |
| **Hardware** | EdgeBox RPi-200 (8GB/32GB eMMC) | *Nota:* Se requiere almacenamiento externo y Cámara Estéreo (Depth Camera)  con  si se activa RF-D01. |
| **Backend** | Python 3.11 + FastAPI (Async) | Manejo concurrente de I/O (Serial, Red) sin bloqueos. |
| **Base de Datos** | MariaDB (InnoDB) | Robustez transaccional para datos críticos. |
| **Agente IA** | Llama.cpp + Qwen 2.5 3B (GGUF) | Agente con capacidad de *Function Calling* en <3GB RAM. |
| **Frontend** | HTML5 + HTMX + WebSockets | Interfaz ligera, actualizaciones en tiempo real sin recarga. |

***