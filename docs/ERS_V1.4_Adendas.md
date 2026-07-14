# ERS V1.4 — Adendas

> **Versión:** 1.4
> **Fecha:** 2026-07-14
> **Origen:** Solicitud del cliente + propuesta de mejora del flujo de trabajo
> **Alcance:** Este documento extiende el [ERS V1.3](Especificación%20de%20Requisitos%20de%20Software%20\(ERS\)%20V1.3.md) con nuevos requerimientos funcionales (RF) derivados de:
> - Solicitud de reportes SMS enriquecidos y alertas automáticas (julio 2026)
> - Integración de cámara para inspección visual de muestras (dataset IA)

---

## Sección A — Reportes SMS Enriquecidos y Alertas Automáticas

> **Restricción:** Los corresponsales solo acceden a SIP-Edge vía SMS (módem 4G Quectel EC25). No hay acceso Ethernet en campo. Toda entrega de información es texto plano.

### A.1 — Filtros y agrupación

| ID | Requerimiento |
|----|--------------|
| **RF-V14-01** | CUANDO un corresponsal solicita un reporte, el sistema DEBE aceptar rangos de fecha mediante shortcuts: \`hoy\`, \`ayer\`, \`últimos 7 días\`, \`mes actual\`, o fechas personalizadas \`YYYY-MM-DD\` a \`YYYY-MM-DD\`. |
| **RF-V14-02** | CUANDO un corresponsal solicita un reporte, el sistema DEBE aceptar un parámetro de agrupación: \`día\`, \`semana\`, \`mes\`, o \`turno\` (mañana/tarde/noche/madrugada). |
| **RF-V14-03** | CUANDO un corresponsal solicita filtrar por vehículo, el sistema DEBE aceptar \`tractomula\` y/o \`vagon\` como parámetros opcionales en las herramientas de consulta. |

### A.2 — Nuevas métricas de operación

| ID | Requerimiento |
|----|--------------|
| **RF-V14-04** | El sistema DEBE calcular el tiempo promedio entre pesajes consecutivos en un rango de fechas (\`get_avg_weighing_time\`). |
| **RF-V14-05** | El sistema DEBE calcular la tasa de rechazo como el porcentaje de pesajes con anomalías detectadas vs. el total de pesajes en un rango de fechas (\`get_anomaly_rate\`). |
| **RF-V14-06** | El sistema DEBE retornar un ranking de las N haciendas con mayor peso total acumulado en un rango de fechas (\`get_top_haciendas\`). |
| **RF-V14-07** | El sistema DEBE calcular el comparativo entre un período actual y el período inmediatamente anterior del mismo tamaño, retornando la diferencia absoluta (Δ) y el cambio porcentual (Δ%) para cada métrica (\`get_period_comparison\`). |
| **RF-V14-08** | La desviación estándar ya existe en \`get_basic_stats\`. El sistema DEBE incluirla en los resúmenes SMS cuando sea relevante. |

### A.3 — Alertas estadísticas automáticas

| ID | Requerimiento |
|----|--------------|
| **RF-V14-09** | CUANDO el Z-Score de un pesaje supera el umbral configurable (\`anomaly_threshold_pct\`, default 15%), el sistema DEBE enviar un SMS de alerta al administrador indicando operador, peso, hacienda y valor Z. |
| **RF-V14-10** | CUANDO la cantidad de pesajes del día actual cae más del porcentaje configurable (\`production_drop_pct\`, default 20%) respecto al promedio móvil de los últimos 7 días, el sistema DEBE enviar un SMS de alerta al administrador. |
| **RF-V14-11** | CUANDO un pesaje está fuera de 3 desviaciones estándar de la media de la ventana móvil, el sistema DEBE enviar un SMS de alerta de outlier. |
| **RF-V14-12** | CUANDO transcurren más de N minutos (\`inactivity_minutes\`, default 120) sin registrar pesajes durante el horario laboral activo, el sistema DEBE enviar un SMS de alerta de inactividad. |
| **RF-V14-13** | El sistema DEBE evitar el envío duplicado de la misma alerta: si ya se envió una alerta para una condición y esta persiste, NO DEBE reenviarse hasta que se resuelva y vuelva a ocurrir. |
| **RF-V14-14** | Todos los umbrales de alerta DEBEN ser configurables en \`config.yaml\` bajo la sección \`alerts:\`, incluyendo: \`anomaly_threshold_pct\`, \`production_drop_pct\`, \`inactivity_minutes\`, \`outlier_stddev\`, \`check_interval_minutes\`, \`active_hours_weekday\`, \`active_hours_saturday\`. |

### A.4 — Programación y entrega SMS

| ID | Requerimiento |
|----|--------------|
| **RF-V14-15** | El sistema DEBE enviar un SMS diario a las 6:00 am (hora Bogotá) con el resumen del día anterior: cantidad de pesajes, promedio de peso total, top 3 haciendas, anomalías detectadas. |
| **RF-V14-16** | El sistema DEBE evaluar condiciones de alerta cada 4 horas durante el horario activo. SI hay novedades (anomalías, caída, outliers, inactividad) ENTONCES DEBE enviar SMS. Si no hay novedades, NO DEBE enviar nada. |
| **RF-V14-17** | El sistema DEBE enviar un SMS cada lunes a las 7:00 am (hora Bogotá) con el resumen semanal: tendencia de pesos, comparativo vs semana anterior, desviación estándar, top haciendas. |
| **RF-V14-18** | Todo SMS de reporte DEBE incluir un resumen ejecutivo de 3 líneas al inicio con los KPIs más relevantes (total pesajes, anomalías, cambio vs período anterior). |
| **RF-V14-19** | El sistema DEBE ofrecer plantillas pre-configuradas de reportes: "Reporte Gerencia", "Reporte Operaciones", "Reporte Calidad", cada una con su propio conjunto de métricas, umbrales y horario. |
| **RF-V14-20** | El sistema DEBE usar la zona horaria \`America/Bogota\` (GMT-5) para todo cálculo de horarios de envío, turnos y fechas. |
| **RF-V14-21** | El sistema DEBE aceptar configuración de días activos (ej. L-V \`[1,2,3,4,5]\`, L-S \`[1,2,3,4,5,6]\`) y NO DEBE enviar reportes programados en días inactivos. |
| **RF-V14-22** | El sistema DEBE formatear números en español-Colombia (\`es_CO\`): separador de miles con punto (\`.\`) y decimales con coma (\`,\`). |

### A.5 — Advertencia de rendimiento del LLM local

| ID | Requerimiento |
|----|--------------|
| **NFR-V14-01** | El sistema DEBE documentar que cada nueva herramienta estadística agregada a \`TOOL_DEFINITIONS\` incrementa el tamaño del prompt enviado al LLM (~200-400 tokens por tool), y que el tiempo de inferencia en los modelos locales del EdgeBox (Qwen2.5 1.5B, Gemma 4 2B, Qwen3.5 2B) crece linealmente con el tamaño del prompt. |
| **NFR-V14-02** | El tiempo total de respuesta a una consulta SMS (inferencia LLM + ejecución SQL + envío SMS) DEBE mantenerse dentro de un umbral aceptable de ≤ 60 segundos. Si se excede, DEBE considerarse: (a) usar modelo de mayor capacidad, (b) agrupar herramientas relacionadas, o (c) migrar lógica a heurísticas pre-LLM. |

---

## Sección B — Captura de Imágenes para Inspección Visual de Muestras

> **Contexto:** Después del paso 2 del flujo de pesaje (Leer Muestra = peso total), la muestra se extiende en una bandeja de inspección para hacer visibles todos sus componentes (caña, materia extraña mineral, materia extraña vegetal). Una cámara cenital captura una fotografía que se asocia al registro de pesaje, formando un dataset para entrenar una red neuronal capaz de inferir los pesos desde la imagen.

### B.1 — Hardware de captura

| ID | Requerimiento |
|----|--------------|
| **RF-V14-23** | El sistema DEBE integrar una cámara ReCamera 2002w (SeeedStudio) conectada al EdgeBox mediante WiFi en modo AdHoc. |
| **RF-V14-24** | El sistema DEBE detectar una señal digital en una entrada GPIO del EdgeBox como disparador para capturar la fotografía. |
| **RF-V14-25** | La fotografía DEBE ser tomada desde posición cenital (perpendicular a la bandeja de inspección), capturando la totalidad de la muestra extendida. |

### B.2 — Integración con el flujo de pesaje

| ID | Requerimiento |
|----|--------------|
| **RF-V14-26** | CUANDO el operador completa el paso "Leer Muestra" (peso total), el sistema DEBE habilitar la captura de imagen. La fotografía DEBE tomarse después de extender la muestra en la bandeja de inspección y ANTES de iniciar el paso "Tara Mineral". |
| **RF-V14-27** | El proceso de pesaje (tara, lectura, confirmación) DEBE funcionar de manera independiente al proceso de captura de imágenes. SI la cámara no está disponible o la captura está detenida, el flujo de pesaje NO DEBE verse afectado. |
| **RF-V14-28** | CUANDO se confirma un pesaje, el sistema DEBE asociar la última imagen capturada (si existe) al registro de pesaje mediante un identificador único. |

### B.3 — Almacenamiento

| ID | Requerimiento |
|----|--------------|
| **RF-V14-29** | Las imágenes DEBEN almacenarse en la unidad SSD conectada al EdgeBox en `/mnt/ssd/`, bajo una estructura de subdirectorios por fecha `captures/YYYY-MMM-DD/`. Ejemplo: `/mnt/ssd/captures/2026-jul-14/`. El nombre del mes DEBE usar la abreviatura en español: ene, feb, mar, abr, may, jun, jul, ago, sep, oct, nov, dic. El nombre de archivo DEBE tener el formato `HHMMSS_<id_weighing>.jpg`. |
| **RF-V14-30** | El sistema DEBE mantener una tabla `imagen_captures` en MariaDB que registre: `id`, `weighing_id` (FK), `filename`, `file_path`, `file_size_bytes`, `captured_at`, `ssd_mounted` (bool), `metadata` (JSON con pesos, hacienda, suerte, operador —heredado de `weighings.user_id`—, fecha, tipo_cosecha). |
| **RF-V14-31** | SI la unidad SSD no está montada o está llena, el sistema DEBE almacenar la metadata en `imagen_captures` indicando `ssd_mounted=false` y `file_path=null`, y NOTIFICAR al administrador vía SMS. |

### B.4 — Administración y exportación

| ID | Requerimiento |
|----|--------------|
| **RF-V14-32** | El administrador DEBE poder detener la captura de imágenes mediante un endpoint `POST /api/imaging/stop` sin afectar el proceso de pesaje. |
| **RF-V14-33** | El administrador DEBE poder desmontar lógicamente la unidad SSD desde la aplicación mediante un endpoint `POST /api/imaging/unmount`. Este endpoint DEBE: (a) verificar que la captura está detenida, (b) ejecutar `umount /mnt/ssd` en el sistema, (c) retornar confirmación de desmontaje. El administrador NO DEBE necesitar usar comandos Linux manualmente para esta tarea. |
| **RF-V14-34** | El administrador DEBE poder montar lógicamente la unidad SSD desde la aplicación mediante un endpoint `POST /api/imaging/mount`. Este endpoint DEBE: (a) ejecutar `mount /mnt/ssd`, (b) verificar que el montaje fue exitoso, (c) retornar espacio disponible. El administrador NO DEBE necesitar usar comandos Linux manualmente para esta tarea. |
| **RF-V14-35** | El endpoint `GET /api/imaging/status` DEBE retornar: estado (`active`/`stopped`/`error`), SSD montado (bool), espacio disponible en bytes, cantidad de imágenes capturadas hoy, última captura (timestamp). |
| **RF-V14-36** | El flujo completo de exportación manual DEBE ser: (1) administrador autenticado detiene la captura (`POST /api/imaging/stop`), (2) desmonta lógicamente el SSD desde la app (`POST /api/imaging/unmount`), (3) retira físicamente el SSD, (4) copia las imágenes a otro dispositivo de almacenamiento, (5) reconecta físicamente el SSD al EdgeBox, (6) monta lógicamente el SSD desde la app (`POST /api/imaging/mount`), (7) reanuda la captura (`POST /api/imaging/start`). El sistema DEBE detectar la desconexión y reconexión física del SSD sin fallar. |
| **RF-V14-37** | CUANDO el administrador ejecuta el paso (2) de desmontaje lógico (`POST /api/imaging/unmount`), el sistema DEBE registrar automáticamente en `imagen_captures` los campos `exported_at` (timestamp del desmontaje) y `exported_by` (user_id del admin autenticado que ejecutó la acción) para todas las imágenes cuyo `exported_at` sea NULL. **Nota:** El operador que realizó las medidas de peso y la imagen NO se identifica aquí — ese dato ya está en `weighings.user_id` (FK desde `imagen_captures.weighing_id`) y se replica en el JSON `metadata.operador`. |

### B.5 — Dataset para red neuronal

| ID | Requerimiento |
|----|--------------|
| **RF-V14-38** | Cada imagen DEBE estar asociada a los 3 valores de peso del registro de pesaje correspondiente (`peso_muestra`, `peso_mineral`, `peso_vegetal_extrano`) para conformar un dataset etiquetado de entrenamiento. |
| **RF-V14-39** | Los metadatos exportables DEBEN incluir un archivo `metadata.csv` o `metadata.json` por lote de exportación que contenga: `filename`, `weighing_id`, `fecha`, `hacienda_codigo`, `suerte_codigo`, `tipo_cosecha`, `peso_muestra`, `peso_mineral`, `peso_vegetal_extrano`, `operador_nombre`. |

---

## Sección C — No implementable (registro)

Los siguientes items de la solicitud del cliente NO son implementables con la infraestructura actual. Se documentan aquí para trazabilidad y para evitar que se soliciten nuevamente sin un cambio en las condiciones técnicas.

| Ítem | Motivo |
|------|--------|
| Gráficos PNG (tendencia, barras, torta) | SMS solo transporta texto. Sin acceso Ethernet para servir imágenes por otro canal. |
| Archivos adjuntos Excel/CSV | SMS no transporta archivos. Sin canal alternativo. |
| Archivos adjuntos PDF | SMS no transporta binarios. Sin canal alternativo. |
| Tablas formateadas (celdas, colores, alineación) | SMS es texto plano; solo permite formato ASCII rudimentario. |
| Dashboard web para corresponsales | Sin acceso Ethernet en campo. |
| Filtro por "Destino" | Toda la caña va a la misma fábrica. El filtro no aporta valor. |
| Filtro por "Proveedor" | Ya cubierto por el filtro de Hacienda existente (el cliente usó "proveedor" como sinónimo). |
| OEE de báscula (Disponibilidad × Rendimiento × Calidad) | Requiere sensores de uptime/downtime, velocidad nominal y tasa de defectos. Infraestructura no existe. |

---

## Sección D — Features derivadas

Los RF de esta adenda se implementarán en las siguientes features:

| Feature ID | Nombre | RF cubiertos | Depende de |
|-----------|--------|-------------|-----------|
| **F29** | `sql_tools_v2` | RF-V14-01 al RF-V14-08 | F8 (done) |
| **F30** | `alert_monitor` | RF-V14-09 al RF-V14-14, NFR-V14-01, NFR-V14-02 | F29, F7 (done) |
| **F31** | `sms_scheduling_v2` | RF-V14-15 al RF-V14-22 | F30, F27 (done) |
| **F32** | `sample_imaging` | RF-V14-23 al RF-V14-39 | F6, F13 (done) |

> **Nota:** Los spec-authors de cada feature referenciarán los RF de esta adenda. Los RF con prefijo `NFR` son no-funcionales y se verifican en la revisión de arquitectura, no mediante tests unitarios.
