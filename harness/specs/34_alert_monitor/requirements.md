# Requirements — AlertMonitor

> Feature 34: Monitor de Alertas Automáticas
> ERS Ref: ERS_V1.4_Adendas.md §A.3 (RF-V14-09 al RF-V14-14), §A.5 (NFR-V14-01, NFR-V14-02)

---

## R1 — Materia extraña excesiva
CUANDO el sistema ejecuta una evaluación periódica y encuentra uno o más pesajes donde `(peso_mineral + peso_vegetal_extrano) / peso_muestra` supera el umbral `materia_extrana_pct` (default 0.15), el sistema DEBE generar una alerta de tipo `materia_extrana` en la tabla `alert_log` con severity `warning`.

## R2 — Anomalía Z-Score
CUANDO el sistema ejecuta una evaluación periódica y encuentra uno o más pesajes cuyo Z-Score del peso total `(peso_muestra + peso_mineral + peso_vegetal_extrano)` supera `z_threshold` (default 3.0) respecto a la ventana móvil configurada (`zscore_window_size`, default 120; `zscore_window_hours`, default 4), el sistema DEBE generar una alerta de tipo `zscore_anomaly` en la tabla `alert_log` con severity `warning`.

> **Nota:** La detección Z-Score ya existe en `AnomalyDetector._detect_zscore()` y se ejecuta en tiempo real tras cada pesaje. El AlertMonitor la replica en su ciclo periódico para garantizar cobertura completa y generar registros en `alert_log` con el formato unificado de esta feature.

## R3 — Muestra insuficiente
CUANDO el sistema ejecuta una evaluación periódica y encuentra uno o más pesajes donde `peso_muestra < muestra_min_kg` (default 10.0 kg), el sistema DEBE generar una alerta de tipo `muestra_insuficiente` en la tabla `alert_log` con severity `info`.

## R4 — Caída en el flujo de muestras
CUANDO el sistema ejecuta una evaluación periódica y la cantidad de pesajes del día actual es menor al `(1 - production_drop_pct)` del promedio móvil de pesajes de los últimos `production_drop_window_days` días hábiles (default 7, excluyendo hoy), el sistema DEBE generar una alerta de tipo `production_drop` en la tabla `alert_log` con severity `critical`.

> **Interpretación:** El sistema mide número de pesajes (muestras), no toneladas de caña cosechada. Una caída en la cantidad de pesajes refleja una baja en el flujo de camiones que ingresan a la balanza.

## R5 — Outlier 3 sigma
CUANDO el sistema ejecuta una evaluación periódica y encuentra un pesaje donde el peso total `(peso_muestra + peso_mineral + peso_vegetal_extrano)` está fuera de `outlier_stddev` (default 3.0) desviaciones estándar de la media del día actual, el sistema DEBE generar una alerta de tipo `outlier` en la tabla `alert_log` con severity `warning`.

## R6 — Inactividad en horario laboral
CUANDO el sistema ejecuta una evaluación periódica durante horario laboral activo y no hay ningún pesaje registrado en los últimos `inactivity_minutes` (default 120) minutos, el sistema DEBE generar una alerta de tipo `inactivity` en la tabla `alert_log` con severity `warning`.

## R7 — Deduplicación de alertas activas
MIENTRAS exista una alerta activa (status = `active`) para una combinación de `alert_type` en la tabla `alert_log`, el sistema NO DEBE generar una nueva alerta del mismo tipo hasta que la alerta existente sea resuelta.

## R8 — Resolución de alertas
CUANDO el sistema ejecuta una evaluación periódica y la condición que disparó una alerta activa ya no se cumple, el sistema DEBE marcar dicha alerta como `resolved` estableciendo `resolved_at` al timestamp actual.

## R9a — Envío de SMS al administrador
CUANDO se genera una alerta nueva en la tabla `alert_log` (status = `active`, sent_sms = `FALSE`), el sistema DEBE enviar un SMS de alerta a todos los números en `admin_phones` de la configuración SMS.

## R9b — Marcado de SMS enviado
CUANDO el SMS de una alerta es enviado exitosamente, el sistema DEBE marcar `sent_sms = TRUE` en el registro de alerta correspondiente.

## R10 — Evaluación periódica configurable
El sistema DEBE ejecutar la evaluación de condiciones de alerta cada `check_interval_minutes` minutos (default 15) durante el horario laboral activo.

## R11 — Configuración de umbrales en config.yaml
Todos los umbrales de alerta DEBEN ser configurables en `config.yaml` bajo la sección `alerts:`, incluyendo al menos: `materia_extrana_pct`, `z_threshold`, `zscore_window_size`, `zscore_window_hours`, `muestra_min_kg`, `production_drop_pct`, `production_drop_window_days`, `outlier_stddev`, `inactivity_minutes`, `check_interval_minutes`, `active_hours_weekday`, `active_hours_saturday`.

## R12 — Persistencia de alertas en tabla alert_log
El sistema DEBE persistir cada alerta generada en la tabla `alert_log` con los siguientes campos: `id`, `alert_type`, `severity`, `metric_value`, `threshold`, `detail`, `status`, `sent_sms`, `resolved_at`, `created_at`.

## R13a — Horario laboral lunes a viernes
CUANDO el día actual es lunes a viernes, el sistema DEBE usar `active_hours_weekday` para determinar si la hora actual está dentro del horario laboral activo.

## R13b — Horario laboral sábado
CUANDO el día actual es sábado, el sistema DEBE usar `active_hours_saturday` para determinar si la hora actual está dentro del horario laboral activo.

## R13c — Horario domingo
CUANDO el día actual es domingo, el sistema NO DEBE evaluar condiciones de inactividad ni producción.

## R14 — Documentación del impacto en prompt del LLM (NFR-V14-01)
El `design.md` y la implementación DEBEN documentar que las herramientas estadísticas agregadas al catálogo `TOOL_DEFINITIONS` incrementan el tamaño del prompt del LLM local (~200-400 tokens por tool), impactando el tiempo de inferencia en los modelos del EdgeBox (Qwen2.5 1.5B, Gemma 4 2B, Qwen3.5 2B).

## R15a — Tiempo de respuesta SMS ≤ 60 segundos (NFR-V14-02)
El tiempo total desde que se dispara una condición de alerta hasta que el SMS es enviado DEBE mantenerse por debajo de 60 segundos.

## R15b — Registro de timeout SMS
SI el tiempo de respuesta SMS excede 60 segundos ENTONCES el sistema DEBE registrar una advertencia en los logs.
