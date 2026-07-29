# Propuesta Comercial — SIP-Edge NextGen

> Plataforma Inteligente de Borde para Laboratorios y Control de Calidad en la Industria
> Agroindustrial, con Inteligencia Artificial Local y Comunicación en Tiempo Real vía Telegram.

**Versión:** 1.0 — Julio 2026
**Dirigido a:** Gerentes de Operaciones, Directores de Calidad, CTOs del sector agroindustrial.

---

## 1. Resumen Ejecutivo

**SIP-Edge NextGen** es una plataforma de *edge computing* que digitaliza, automatiza y hace
inteligente el proceso de control de calidad en laboratorios industriales. Opera de forma
100% autónoma en hardware de bajo consumo (EdgeBox ARM), sin dependencia de internet, y
reemplaza la comunicación SMS por **Telegram** para una experiencia más rica, inmediata y
sin costo por mensaje.

El sistema ya ha sido probado en producción durante meses en un ingenio azucarero colombiano
(Ingenio Mayagüez S.A.) con resultados validados: **29/29 requisitos contractuales
entregados al 100%, 16 funcionalidades adicionales sobre el alcance original, 0 bugs
pendientes en producción.**

### ¿Qué lo hace diferente?

| Característica | Sistemas tradicionales | SIP-Edge NextGen |
|---------------|----------------------|------------------|
| **Conectividad** | Depende de internet y servidores centrales | Opera 100% offline en el borde |
| **Consulta de datos** | Interfaces web complejas, comandos rígidos | Lenguaje natural vía Telegram ("¿cómo va el turno?") |
| **Detección de problemas** | Manual, después del hecho | Automática en tiempo real con IA local (3 capas de análisis) |
| **Costo operativo** | SMS tarifado por mensaje, servidores cloud | Telegram gratuito, hardware local de $300 |
| **Escalabilidad** | Por usuario/servidor | Misma caja soporta crecimiento sin costo adicional |
| **Curva de aprendizaje** | Alta (capacitación requerida) | Cero — se usa como WhatsApp |

---

## 2. El Problema que Resolvemos

En los laboratorios de control de calidad de la industria agroindustrial (caña de azúcar,
palma de aceite, café, arroz, frutas) ocurre lo siguiente **todos los días**:

1. **Datos atrapados en papel o Excel.** Los operadores anotan pesos de báscula en
   planillas físicas. Los supervisores no tienen visibilidad en tiempo real.

2. **Errores de transcripción.** Un número mal copiado, un decimal corrido, una hacienda mal
   registrada. Sin trazabilidad, sin auditoría.

3. **Anomalías no detectadas.** Un lote con contaminación anormalmente alta se procesa sin
   que nadie lo note hasta que el cliente reclama.

4. **Supervisores a ciegas.** El gerente de operaciones está a 50 km del laboratorio.
   Depende de una llamada telefónica o una visita para saber cómo va el turno.

5. **Procesos manuales de reportes.** Alguien dedica 30-60 minutos al final del turno a
   consolidar planillas para generar un informe. Todos los días. Tres turnos por día.

**SIP-Edge NextGen elimina cada uno de estos puntos** con un sistema que corre solo, en una
caja del tamaño de un libro, sin requerir internet ni servidores externos.

---

## 3. La Solución: ¿Qué Hace SIP-Edge NextGen?

### 3.1 Vista general del flujo de trabajo

```
┌─────────────┐     ┌──────────────────┐     ┌────────────────┐
│ Báscula     │────▶│  EdgeBox ARM     │────▶│  PC externo    │
│ industrial  │ RS485│  (SIP-Edge)     │ RS232│  (sistema      │
│ (RS485)     │     │                  │     │   legacy)      │
└─────────────┘     │  • IA local      │     └────────────────┘
                    │  • Base de datos │
┌─────────────┐     │  • Telegram bot  │     ┌────────────────┐
│ Cámara      │────▶│  • Web UI kiosco │────▶│  Supervisor    │
│ cenital     │WiFi │                  │Telegram│  (donde esté) │
│ (opcional)  │     └──────────────────┘     └────────────────┘
```

1. El operador interactúa con una pantalla táctil en modo kiosco industrial.
2. La báscula envía pesos automáticamente al sistema (sin teclear).
3. Los datos se almacenan en base de datos local con integridad transaccional.
4. Una IA local analiza cada pesaje y detecta anomalías automáticamente.
5. Supervisores y gerentes consultan datos en **lenguaje natural por Telegram**.
6. Reportes programados llegan automáticamente a los interesados.
7. Opcionalmente, una cámara captura imágenes para entrenar modelos de visión artificial.

### 3.2 Módulos del sistema

| Módulo | ¿Qué hace? | Valor |
|--------|-----------|-------|
| **Kiosco de Pesaje** | Interfaz táctil para el operador. 3 pasos guiados: Tara → Leer Muestra → Confirmar. | Elimina el papel. Reduce errores de captura a cero. |
| **Integración Serial** | Lectura directa de báscula industrial por RS485. Transmisión automática a PC externo por RS232. | El peso nunca se digita. La trama viaja automáticamente al sistema legacy del cliente. |
| **Gestión de Datos Maestros** | CRUD de haciendas/proveedores, suertes/lotes, usuarios, roles. | Un solo lugar para administrar todo. Trazabilidad completa de quién creó qué. |
| **Autenticación y RBAC** | JWT + bcrypt. Tres roles: admin (total), operador (solo pesaje), corresponsal (solo consultas). | Seguridad granular. Bloqueo por inactividad configurable. |
| **Inteligencia Artificial** | LLM local (modelo de lenguaje) + 16 herramientas SQL. | Los usuarios consultan en lenguaje natural. El sistema detecta anomalías automáticamente. |
| **Comunicación Telegram** | Bot bidireccional. Comandos, consultas, reportes, alertas. | Reemplaza SMS con costo cero. Soporta texto enriquecido, archivos adjuntos (PDF, imágenes). |
| **Reportes y Alertas** | Programación diaria/semanal/condicional. Plantillas pre-configuradas. | Los gerentes reciben resúmenes sin pedirlos. Alertas automáticas ante desviaciones. |
| **Respaldos** | Volcado diario con rotación FIFO 30 días. Exportación a USB/SD con verificación CRC32. | Datos seguros. Cumplimiento de normas de retención. |
| **Modo Manual de Emergencia** | El operador solicita desde el kiosco. El supervisor autoriza remotamente. | Continuidad operativa ante fallo de báscula. Sin parar la producción. |
| **Captura de Imágenes** (opcional) | Cámara cenital disparada por GPIO. Asociación automática imagen↔pesaje. | Dataset etiquetado para entrenar redes neuronales de visión artificial. |

---

## 4. El Corazón Inteligente: IA que Realmente Funciona

> **Este es el punto de venta más fuerte en el mercado actual.** La inteligencia artificial
> no es un buzzword en SIP-Edge — es una necesidad operativa real, implementada con
> ingeniería responsable.

### 4.1 ¿Por qué un LLM y no comandos tradicionales?

Los supervisores y corresponsales acceden al sistema desde el campo, sin una computadora.
Con SMS tradicional, necesitarían memorizar comandos como:

```
RESUMEN HACIENDA=131 FECHA_INI=2026-07-15 FECHA_FIN=2026-07-22 METRICA=PROMEDIO TIPO=MINERAL
```

Con SIP-Edge NextGen, simplemente escriben en Telegram:

> *"¿cómo ha estado el mineral en la hacienda 131 esta semana?"*

**El LLM invierte el paradigma: el sistema se adapta al usuario, no al revés.**

| Capacidad | Sin IA (comandos fijos) | Con IA (LLM + Function Calling) |
|-----------|------------------------|--------------------------------|
| Sintaxis | Fija, debe memorizarse | Libre, lenguaje natural |
| Errores de tipeo | Rechazo silencioso | Interpreta la intención ("cuantos pesages ubo oy" → entiende) |
| Ambigüedad | No tolerada | Pide aclaración ("¿te refieres al 14 o al 15 de junio?") |
| Contexto conversacional | Cada mensaje independiente | Entiende seguimiento ("¿y ayer?", "¿y la hacienda 123?") |
| Curva de aprendizaje | Alta | Cero (hablar/escribir como siempre) |
| Adopción por usuarios no técnicos | Baja sin entrenamiento | Inmediata |

### 4.2 Railes de seguridad: la IA no alucina con tus datos

**El mayor riesgo de un LLM en un contexto industrial son las alucinaciones numéricas.**
SIP-Edge NextGen lo resuelve con una arquitectura de **Function Calling estricto:**

- El LLM **NUNCA genera valores cuantitativos.** Solo decide *qué herramienta SQL ejecutar*.
- Los números siempre provienen de la base de datos real, ejecutados por código Python determinístico.
- El LLM solo *parafrasea en lenguaje natural* los resultados que ya existen.
- Temperatura 0.1 (mínima creatividad), max_tokens limitado a 512.
- Tool calls con schemas JSON tipados — el LLM no puede inventar herramientas que no existen.
- System prompt con instrucciones estrictas contra invención de datos.
- Auditoría completa: cada tool call queda registrado con argumentos, resultados y duración.

**El resultado:** un sistema que habla como humano pero calcula como máquina.

### 4.3 Detección de anomalías en tiempo real (3 capas)

Cada vez que se confirma un pesaje, el sistema ejecuta automáticamente:

| Capa | ¿Qué analiza? | Ejemplo |
|------|--------------|---------|
| **1 — Z-Score** | Desviación estadística sobre ventana móvil de 120 registros | "Este pesaje está 4.2 desviaciones estándar por encima de la media — puede ser un outlier" |
| **2 — Ratios** | Proporción de materia extraña vs. peso total | "La materia mineral representa el 45% de la muestra cuando el umbral es 30%" |
| **3 — Temporal** | Tasa de cambio y rachas | "Los últimos 4 pesajes consecutivos superan el umbral — hay un patrón sistemático" |

Si se detecta una anomalía, el sistema:
1. Genera un reporte narrativo con IA explicando el hallazgo.
2. Envía una alerta inmediata por Telegram al supervisor.
3. Registra el evento en la bitácora de anomalías para auditoría.

**Esto ocurre en segundos, sin intervención humana, 24/7.**

### 4.4 Catálogo de herramientas analíticas (16 tools)

Los usuarios pueden consultar por Telegram:

| Herramienta | ¿Qué responde? |
|-------------|---------------|
| Estadísticas básicas | Media, mediana, desviación estándar, min, max por período |
| Percentiles | Distribución de pesos (P25, P50, P75, P90, P95) |
| Media móvil | Tendencia suavizada en ventana de N registros |
| Tendencia | Evolución temporal de cualquier métrica |
| Desglose por hacienda | Ranking de proveedores por peso, anomalías, composición |
| Desglose por operador | Productividad y calidad por turno/operador |
| Composición de materiales | Proporción muestra/mineral/vegetal |
| Resumen de turno | KPIs consolidados (mañana/tarde/noche/madrugada) |
| Resumen diario | Totales, promedios, anomalías del día |
| Comparativo de períodos | Δ y Δ% vs. semana/mes anterior |
| Detección de anomalías | Lista de anomalías detectadas con Z-Score y detalle |
| Verificación de umbrales | ¿Algún indicador excedió su límite? |
| Tiempo promedio de pesaje | Eficiencia del operador (ritmo de trabajo) |
| Tasa de rechazo | % de pesajes anómalos vs. total |
| Top haciendas | Ranking de N haciendas por peso total |
| Período personalizado | Métricas agregadas en rango arbitrario de fechas |

---

## 5. Telegram como Canal de Comunicación

> Reemplazamos SMS por Telegram. Mismas capacidades, **costo cero**, experiencia superior.

### 5.1 ¿Qué gana el cliente con Telegram vs. SMS?

| Dimensión | SMS (sistema anterior) | Telegram (NextGen) |
|-----------|----------------------|---------------------|
| **Costo** | ~$0.05-0.10 por mensaje. 200+ mensajes/mes = $20+ | $0. Ilimitado. |
| **Contenido** | Solo texto plano, máximo 160 caracteres | Texto enriquecido, sin límite práctico de longitud |
| **Adjuntos** | Imposible (SMS no transporta archivos) | **PDF, imágenes, gráficos, Excel** adjuntos al mensaje |
| **Entrega** | Depende de señal GSM | Solo requiere internet móvil (4G) |
| **Historial** | Se pierde al cambiar de teléfono | Persiste en la nube de Telegram, multidispositivo |
| **Grupos** | No disponible | Un grupo de Telegram recibe reportes automáticos. Todos los interesados ven lo mismo. |
| **UX** | SMS genérico | Interfaz de chat moderna, multimedia, bots interactivos |

### 5.2 ¿Qué puede hacer el bot de Telegram?

| Funcionalidad | Ejemplo |
|--------------|---------|
| **Consultas en lenguaje natural** | *"¿cuántas toneladas procesó la hacienda 131 esta semana?"* |
| **Comandos de emergencia** | *"manual on"*, *"manual off"*, *"extender 15"* |
| **Restablecimiento de contraseña** | Admin envía *"reset password operador3"* → sistema responde con PIN |
| **Reportes programados** | Lunes 7am: resumen semanal con PDF adjunto. Diario 6am: resumen día anterior. |
| **Alertas automáticas** | *"ALERTA: Pesaje #1247 supera umbral de materia extraña (18.3% > 15%)"* |
| **Conversación multiturno** | *"¿y ayer?"*, *"¿y la hacienda 123?"*, *"gracias"* — con contexto |
| **Archivos adjuntos** | El reporte semanal llega como PDF con gráficos de tendencia y composición |

---

## 6. Stack Tecnológico

> Mismo stack probado en producción durante meses. Software libre. Sin costos de licencia.

| Capa | Tecnología | Justificación |
|------|-----------|---------------|
| **Backend** | Python 3.13 + FastAPI | Async nativo. Ideal para I/O serial y comunicación concurrente. |
| **Frontend** | Svelte 5 + Vite | Compilado a JS puro. Sin runtime. Ideal para kiosco industrial. |
| **Base de datos** | MariaDB 11.8 | Robusta, transaccional, 0 costo de licencia. |
| **IA Local** | llama.cpp + Qwen 2.5 1.5B | Corre en la misma caja. Sin API keys, sin latencia de red, sin costo por consulta. |
| **Comunicación** | Telegram Bot API (long polling) | Sin webhooks, sin abrir puertos. Máxima seguridad. |
| **Hardware** | EdgeBox ARM (Raspberry Pi CM4, 8 GB RAM, 32 GB eMMC) | Bajo consumo (~15W). Tamaño libro. Sin ventilador. |
| **Despliegue** | systemd + Docker Compose (dev) | Arranque automático. Reinicio ante fallos. Watchdog por hardware. |

### 6.1 ¿Por qué IA local y no APIs en la nube (ChatGPT, DeepSeek, etc.)?

| Razón | Explicación |
|-------|------------|
| **Sin internet = sin excusas** | Muchos laboratorios están en zonas rurales sin conectividad confiable. El sistema no puede depender de un servicio externo. |
| **Costo cero operativo** | ChatGPT API cobra ~$0.002/1K tokens. Con 50+ consultas diarias y contexto de herramienta grande, el costo mensual sería significativo. El LLM local cuesta $0. |
| **Latencia predecible** | ~3-5 segundos local vs. 1-10 segundos (variable) en la nube. Consistencia es clave en entorno industrial. |
| **Privacidad total de datos** | Los datos de producción nunca salen de la caja. Cumplimiento de normas de confidencialidad corporativa. |
| **No hay dependencia de un tercero** | Si OpenAI cambia precios, depreca modelos o tiene outage, el sistema sigue funcionando. |
| **Personalizable** | Se puede afinar el system prompt, cambiar el modelo, o usar fine-tuning sin depender de un proveedor externo. |

---

## 7. Funcionalidades Incluidas (Alcance Completo)

### 7.1 Ya probadas en producción (sistema base SIP-Edge)

| # | Funcionalidad | Estado |
|---|--------------|--------|
| 1 | Configuración dinámica de puertos hardware (RS485, RS232) con prueba de conectividad | ✅ Producción |
| 2 | Autenticación JWT + RBAC (admin, operador, corresponsal) + bloqueo por inactividad | ✅ Producción |
| 3 | CRUD de usuarios con activación/desactivación lógica | ✅ Producción |
| 4 | Gestión de haciendas/proveedores y suertes/lotes con borrado lógico | ✅ Producción |
| 5 | Integración serial bidireccional con báscula industrial (protocolo DINI ARGEO) | ✅ Producción |
| 6 | Captura de pesaje multipaso (Tara → Leer → Confirmar) con integridad transaccional | ✅ Producción |
| 7 | Transmisión automática RS232 al PC externo con formato CSV | ✅ Producción |
| 8 | Persistencia y despacho de mensajes (Telegram) con cola asíncrona | ✅ Producción |
| 9 | Restablecimiento de contraseña remoto (PIN de 4 dígitos) | ✅ Producción |
| 10 | Modo manual de emergencia (solicitud kiosco → autorización remota → extensión) | ✅ Producción |
| 11 | Respaldos automáticos diarios con rotación FIFO 30 días + exportación USB/SD | ✅ Producción |
| 12 | Orquestador IA central + 16 herramientas SQL + date anchoring | ✅ Producción |
| 13 | Detección de anomalías en 3 capas (Z-Score + ratios + temporal) | ✅ Producción |
| 14 | Conversaciones multiturno con contexto (FIFO 10 exchanges) | ✅ Producción |
| 15 | Frontend SPA completo: login, kiosco, admin dashboard, reportes, analíticas | ✅ Producción |
| 16 | Reset individual por campo de peso (corregir una lectura sin perder las otras) | ✅ Producción |
| 17 | Campo de notas colapsable + tipo de cosecha en registro de pesaje | ✅ Producción |
| 18 | Paginación en todas las tablas (usuarios, backups, haciendas, suertes) | ✅ Producción |
| 19 | Gestión de haciendas/suertes desde el kiosco (operador) + trazabilidad created_by | ✅ Producción |
| 20 | Búsqueda por código de hacienda con autocompletado en kiosco | ✅ Producción |
| 21 | Herramientas estadísticas v2: shortcuts de fecha, agrupación, filtro por vehículo | ✅ Producción |
| 22 | Identidad corporativa (logos, colores, tipografía, página About, favicon) | ✅ Producción |
| 23 | Reenvío de datos RS232 post-confirmación (botón Reenviar Datos) | ✅ Producción |

### 7.2 Nuevas para NextGen (no implementadas en el sistema base)

| # | Funcionalidad | Valor |
|---|--------------|-------|
| 24 | **Canal Telegram completo** reemplazando SMS — bot bidireccional con todas las capacidades | Eliminación de costo SMS. Adjuntos PDF/gráficos. Grupos de Telegram. |
| 25 | **Monitor de alertas automáticas** — 5 condiciones evaluadas periódicamente: % materia extraña, caída de producción, outliers, inactividad, muestra insuficiente | El supervisor no tiene que revisar nada. El sistema avisa cuando algo anda mal. |
| 26 | **Programación de reportes enriquecida** — diario (6am), condicional (cada 4h si hay novedades), semanal (lunes 7am). Plantillas pre-configuradas (Gerencia, Operaciones, Calidad). | Cada interesado recibe exactamente lo que necesita, cuando lo necesita. |
| 27 | **Informes PDF con gráficos** — tendencia (líneas), composición (torta), KPIs tabulados. Adjuntos al mensaje de Telegram. | De WhatsApp a PDF ejecutivo. Sin abrir Excel ni hacer copy-paste. |
| 28 | **Captura de imágenes para IA visual** — cámara cenital + GPIO + asociación automática imagen↔pesaje + dataset etiquetado para entrenar redes neuronales | La base para el siguiente salto: inspección visual automática con computer vision. |
| 29 | **Dashboard de indicadores en tiempo real** — KPIs en pantalla del kiosco/supervisor | Visibilidad inmediata del estado operativo. |

---

## 8. ¿Qué Recibe el Cliente?

### 8.1 Entregables de software

| Entregable | Descripción |
|-----------|-------------|
| **Sistema SIP-Edge NextGen** | Código fuente completo + scripts de despliegue automatizado |
| **Imagen de sistema pre-configurada** | EdgeBox lista para encender y operar (OS + dependencias + SIP-Edge + llama.cpp + Telegram bot) |
| **Documentación técnica** | 6 informes técnicos (hardware, entorno, backend, frontend, IA, trazabilidad) + SDD + manual de instalación + manual de administración |
| **Pruebas automatizadas** | Suite completa de tests unitarios e integración (~15,000 líneas, cobertura >90%) |

### 8.2 Entregables de hardware (opcional)

| Item | Especificación |
|------|---------------|
| EdgeBox-RPI-200 | 8 GB RAM, 32 GB eMMC, ARM Cortex-A72 x4 |
| Pantalla táctil industrial | 7" o 10", compatible con entorno de laboratorio |
| Conversor RS232 ↔ RS485 | Para conexión con báscula DINI ARGEO |
| Cámara cenital (opcional) | ReCamera 2002w con WiFi y GPIO |
| SSD externo (opcional) | Para almacenamiento de imágenes de entrenamiento IA |

### 8.3 Servicios incluidos

| Servicio | Descripción |
|---------|-------------|
| **Instalación y puesta en marcha** | Configuración in-situ del EdgeBox, báscula, cámara y Telegram bot |
| **Capacitación** | 2 sesiones: operadores (1h) + administradores (2h) |
| **Garantía** | 3 meses de soporte correctivo (bugs) |
| **Personalización corporativa** | Logos, colores, tipografía, página About con disclaimers legales |

---

## 9. Modelo de Inversión

> Nota: Las cifras a continuación son referenciales. Una cotización formal requiere un
> levantamiento detallado de requisitos específicos del cliente.

### 9.1 Inversión estimada por componentes

| Componente | Rango estimado | Notas |
|-----------|---------------|-------|
| **Desarrollo de software** | $18,000 - $28,000 USD | Incluye migración SMS→Telegram + features nuevas. Varía según alcance exacto. |
| **Hardware** | $500 - $800 USD | EdgeBox + pantalla + conversores + cámara (opcional) |
| **Instalación y capacitación** | $2,000 - $4,000 USD | In-situ. Varía según ubicación geográfica. |
| **Soporte extendido (anual)** | $3,600 - $6,000 USD/año | Mantenimiento correctivo + preventivo + actualizaciones |

### 9.2 Retorno de inversión (ROI) estimado

| Fuente de ahorro | Estimado anual |
|-----------------|---------------|
| Eliminación de planillas en papel y transcripción manual | $1,200 - $2,400 |
| Reducción de errores de captura (re-procesos, reclamos) | $3,000 - $8,000 |
| Automatización de reportes (30 min/día × 3 turnos × salario) | $4,500 - $7,500 |
| Detección temprana de anomalías (lotes rechazados evitados) | $5,000 - $15,000 |
| Eliminación de costo SMS (200+ mensajes/mes) | $240 - $600 |
| **Total estimado** | **$13,940 - $33,500 / año** |

**Período de recuperación típico: 6-12 meses.**

---

## 10. ¿Por Qué Elegirnos?

### 10.1 Evidencia de ejecución (track record)

- **29 de 29 requisitos contractuales** entregados al 100% en el proyecto base.
- **16 funcionalidades adicionales** desarrolladas sin costo extra, como respuesta a necesidades operativas detectadas en campo.
- **9 bugs corregidos** — todos documentados con causa raíz, prueba de reproducción y verificación.
- **~25,000 líneas de código** entre backend y frontend, con **15,000 líneas de tests** (ratio 1.56:1 test/código).
- **45+ endpoints REST**, **12 tablas de base de datos**, **20 migraciones**.
- **Meses en producción** sin incidencias críticas. Watchdog por hardware. Recuperación automática ante fallos.

### 10.2 Diferenciadores técnicos

| Diferenciador | Por qué importa |
|--------------|----------------|
| **IA local, no cloud** | Sin dependencia de internet. Sin costo por consulta. Datos 100% privados. |
| **Edge computing real** | Todo corre en una caja de $300. Sin servidores, sin suscripciones, sin vendor lock-in. |
| **Function Calling estricto** | La IA no alucina. Arquitectura diseñada para eliminar el mayor riesgo de LLMs en entornos industriales. |
| **Telegram como canal único** | Consolida consultas, comandos, reportes, alertas y archivos adjuntos en una sola plataforma que los usuarios ya conocen. |
| **Cero dependencias externas** | Software 100% libre. Sin licencias. El cliente es dueño del código. |
| **Metodología SDD (Spec-Driven Development)** | Cada funcionalidad tiene spec, diseño, tasks, implementación y revisión independiente. Trazabilidad completa requisito ↔ test. |

### 10.3 Flexibilidad y adaptabilidad

El sistema base fue diseñado para laboratorios de caña de azúcar, pero la arquitectura es
**genérica y configurable**:

| Elemento configurable | Ejemplos de adaptación |
|----------------------|----------------------|
| **Tipo de material** | Caña, palma, café, arroz, frutas, minerales |
| **Flujo de pesaje** | 1, 2 o 3 pasos. Con o sin tara. Con o sin cámara. |
| **Unidades** | kg, g, toneladas, libras |
| **Entidades de negocio** | Haciendas, proveedores, fincas, cooperativas, frentes de corte |
| **Roles y permisos** | Admin, supervisor, operador, auditor, consulta externa |
| **Canales de comunicación** | Telegram, SMS, o ambos en simultáneo |
| **Idioma y formato regional** | Español, portugués, inglés. Formatos de número y fecha locales. |

---

## 11. Próximos Pasos

1. **Reunión de alcance** (1-2 horas) — Entender sus procesos específicos, puntos de dolor,
   infraestructura existente, integraciones requeridas.
2. **Demo técnica** (1 hora) — Mostrar el sistema base en funcionamiento. Recorrer el flujo
   completo: pesaje → consulta por Telegram → reportes → alertas.
3. **Propuesta formal** — Documento de especificación de requisitos (ERS) + cotización
   detallada + cronograma.
4. **Desarrollo** (8-12 semanas) — Metodología SDD con entregas incrementales. El cliente
   ve avances semanalmente.
5. **Despliegue y capacitación** (1-2 días in-situ) — Instalación, pruebas de aceptación,
   capacitación a operadores y administradores.
6. **Soporte post-entrega** — 3 meses de garantía + soporte extendido opcional.

---

## 12. Contacto

Para agendar una reunión de alcance o solicitar una demo técnica:

- **Email:** [pendiente]
- **Teléfono:** [pendiente]
- **Sitio web:** [pendiente]

---

*Documento preparado con base en el sistema SIP-Edge desarrollado para Ingenio Mayagüez S.A.
(julio 2026). Las métricas de rendimiento, cobertura y funcionalidades corresponden a
mediciones reales del sistema en producción.*
