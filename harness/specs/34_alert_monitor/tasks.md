# Tasks — AlertMonitor

> Feature 34: Monitor de Alertas Automáticas

---

## Backend — Configuración

- [ ] T1 — Agregar dataclass `AlertConfig` en `src/config.py` con los 12 campos configurables (materia_extrana_pct, z_threshold, zscore_window_size, zscore_window_hours, muestra_min_kg, production_drop_pct, production_drop_window_days, outlier_stddev, inactivity_minutes, check_interval_minutes, active_hours_weekday, active_hours_saturday). Cubre: R11.
- [ ] T2 — Modificar `load_config()` en `src/config.py` para leer sección `alerts:` de config.yaml, instanciando `AlertConfig` con valores del archivo o defaults. Cubre: R11.
- [ ] T3 — Modificar `_atomic_write_sections()` en `src/config.py` para preservar la sección `alerts:` al reescribir config.yaml. Cubre: R11.
- [ ] T4 — Agregar sección `alerts:` en `config.yaml` con los valores por defecto de AlertConfig. Cubre: R11.

## Backend — Modelo de datos

- [ ] T5 — Agregar modelo ORM `AlertLog` en `src/models.py` con campos: id, alert_type, severity, metric_value, threshold, detail, status, sent_sms, resolved_at, created_at, e índices compuestos `(alert_type, status)` y `(created_at)`. Cubre: R12.
- [ ] T6 — Crear migración SQL `database/migrations/2026_07_27_000000_create_alert_log_table.sql`. Cubre: R12.

## Backend — AlertMonitor

- [ ] T7 — Crear clase `AlertMonitor` en `src/alert_monitor.py` con constructor que acepte `db_session_factory`, `sms_service` y `AlertConfig`. Cubre: R1-R13c.
- [ ] T8 — Implementar método `_is_business_hours(weekday_hours, saturday_hours) -> bool` que determine si la hora actual está dentro del horario laboral (lunes-viernes usa weekday_hours, sábado usa saturday_hours, domingo retorna False). Cubre: R13a, R13b, R13c.
- [ ] T9 — Implementar método `_is_alert_active(alert_type) -> bool` que consulte si existe una alerta con mismo `alert_type` y `status='active'`. Cubre: R7.
- [ ] T10 — Implementar método `_create_alert(alert_type, severity, metric_value, threshold, detail) -> int | None` que persista en `alert_log` si no hay alerta activa del mismo tipo. Cubre: R7, R12.
- [ ] T11 — Implementar método `_resolve_alert(alert_type)` que marque alertas activas del tipo dado como `resolved`. Cubre: R8.
- [ ] T12 — Implementar método `_check_materia_extrana()` que ejecute SQL query: `SELECT ... FROM weighings WHERE fecha = today AND (peso_mineral + peso_vegetal_extrano) / peso_muestra > materia_extrana_pct`. Genere alertas vía `_create_alert()` para cada pesaje que supere el umbral. Las alertas previas del mismo tipo se resuelven si ya no hay violaciones. Cubre: R1.
- [ ] T13 — Implementar método `_check_zscore()` que calcule Z-Score del peso total `(peso_muestra + peso_mineral + peso_vegetal_extrano)` de cada pesaje del día contra la ventana móvil configurada (media y std de los últimos `zscore_window_size` pesajes, limitados a `zscore_window_hours` horas). Genere alertas tipo `zscore_anomaly` para cada pesaje con |Z| > `z_threshold`. Cubre: R2.
- [ ] T14 — Implementar método `_check_muestra_insuficiente()` que busque pesajes con `peso_muestra < muestra_min_kg`. Genere alertas tipo `muestra_insuficiente`. Cubre: R3.
- [ ] T15 — Implementar método `_check_production_drop()` que compare el conteo de pesajes de hoy contra el promedio diario de los últimos `production_drop_window_days` días hábiles (excluyendo hoy). Si la caída > `production_drop_pct`, genere alerta tipo `production_drop`. Cubre: R4.
- [ ] T16 — Implementar método `_check_outliers()` que calcule media y desviación estándar del peso total de los pesajes del día actual, y detecte pesajes que estén fuera de `outlier_stddev` desviaciones. Genere alertas tipo `outlier`. Cubre: R5.
- [ ] T17 — Implementar método `_check_inactivity()` que verifique si el pesaje más reciente es anterior a `now - inactivity_minutes`, o si no hay pesajes hoy. Solo evalúa si `_is_business_hours()` es True. Genere alerta tipo `inactivity`. Cubre: R6.
- [ ] T18 — Implementar método `_send_sms_for_alert(alert_id, alert_type, detail)` que construya el texto del SMS y llame a `sms_service.send_alert_to_admins()`, luego actualice `sent_sms = True`. Cubre: R9a, R9b.
- [ ] T19 — Implementar método `_check_all_conditions()` que ejecute las 6 verificaciones secuencialmente y luego resuelva alertas de tipos que ya no tienen condiciones activas. Cubre: R8.
- [ ] T20 — Implementar método `start()` y `stop()` para el loop asíncrono, y `_evaluation_loop()` que ejecute `_check_all_conditions()` cada `check_interval_minutes` (con sleep asíncrono). Cubre: R10.

## Backend — Integración en main.py

- [ ] T21 — En `lifespan` de `src/main.py`, inicializar `AlertMonitor` con `db_session_factory`, `sms_service` y `alert_config`; llamar a `start()` y registrar `stop()` en cleanup. Cubre: R10.
- [ ] T22 — Cargar `AlertConfig` desde `load_config()` y almacenarlo en `app.state.alert_config`. Cubre: R11.

## Backend — Endpoint API

- [ ] T23 — Crear `alerts_router` con endpoint `GET /api/alerts/history` que retorne historial paginado de `alert_log`, con filtros opcionales `status` y `alert_type`. Cubre: R12.
- [ ] T24 — Registrar `alerts_router` en `main.py`. Cubre: R12.

## Tests

- [ ] T25 — Crear `tests/test_alert_monitor.py` con clase `TestAlertConfig` que verifique valores por defecto de `AlertConfig` (incluyendo z_threshold=3.0) y carga desde dict. Cubre: R11.
- [ ] T26 — Test: `test_check_materia_extrana_detects_excess` — verificar que un pesaje con ratio > umbral genera alerta. Cubre: R1.
- [ ] T27 — Test: `test_check_materia_extrana_no_alert_when_below` — verificar que no se genera alerta si el ratio está dentro del umbral. Cubre: R1.
- [ ] T28 — Test: `test_check_zscore_detects_anomaly` — verificar que un pesaje con |Z| > z_threshold genera alerta `zscore_anomaly`. Cubre: R2.
- [ ] T29 — Test: `test_check_zscore_no_alert_when_normal` — verificar que un pesaje con |Z| dentro del umbral no genera alerta. Cubre: R2.
- [ ] T30 — Test: `test_check_muestra_insuficiente_detects` — verificar alerta por muestra < mínimo. Cubre: R3.
- [ ] T31 — Test: `test_check_production_drop_detects` — verificar alerta por caída en flujo de muestras. Cubre: R4.
- [ ] T32 — Test: `test_check_outlier_detects` — verificar alerta por outlier 3 sigma. Cubre: R5.
- [ ] T33 — Test: `test_check_inactivity_detects` — verificar alerta por inactividad en horario laboral. Cubre: R6.
- [ ] T34 — Test: `test_deduplication_same_type_active` — verificar que no se crea nueva alerta si ya hay una activa del mismo tipo. Cubre: R7.
- [ ] T35 — Test: `test_resolve_alert_when_condition_clears` — verificar que una alerta activa se resuelve cuando la condición ya no se cumple. Cubre: R8.
- [ ] T36 — Test: `test_send_sms_on_new_alert` — verificar que se llama a `send_alert_to_admins` al crear alerta nueva y que `sent_sms` se marca `TRUE`. Cubre: R9a, R9b.
- [ ] T37 — Test: `test_is_business_hours_weekday` — verificar horario laboral en lunes-viernes. Cubre: R13a.
- [ ] T38 — Test: `test_is_business_hours_saturday` — verificar horario reducido en sábado. Cubre: R13b.
- [ ] T39 — Test: `test_is_business_hours_sunday` — verificar que domingo no es horario laboral. Cubre: R13c.
- [ ] T40 — Test: `test_periodic_evaluation_loop` — verificar que `_check_all_conditions` se llama cada `check_interval_minutes`. Cubre: R10.
- [ ] T41 — Test: `test_alert_log_persistence` — verificar que los registros de alert_log se persisten correctamente en BD. Cubre: R12.

## Documentación

- [ ] T42 — Incluir en el docstring del módulo `src/alert_monitor.py` una nota sobre el impacto de las tools en el prompt del LLM (NFR-V14-01), explicando que AlertMonitor NO agrega tools a TOOL_DEFINITIONS y por lo tanto no impacta el prompt. Cubre: R14.
- [ ] T43 — Agregar test de rendimiento o verificación manual para confirmar que el tiempo de respuesta SMS ≤ 60s. Cubre: R15a.
- [ ] T44 — Implementar logging de advertencia cuando el tiempo de respuesta SMS exceda 60s. Cubre: R15b.
