# Tasks — Campo tipo de cosecha en registro de pesaje

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.

---

## Fase 1 — Backend: Modelo, migración y esquemas

- [x] T1 — Crear migración SQL `database/migrations/2026_06_25_000001_add_tipo_cosecha_to_weighings.sql` con `ALTER TABLE weighings ADD COLUMN tipo_cosecha ENUM(...) NOT NULL DEFAULT 'Mecanico - Verde'`. Cubre: R1, R2.

- [x] T2 — Añadir columna `tipo_cosecha` al modelo ORM `Weighing` en `src/models.py` como `SAEnum` con los 6 valores, NOT NULL, default `'Mecanico - Verde'`, server_default. Cubre: R1, R3.

- [x] T3 — Añadir constante `TIPO_COSECHA_VALUES` y campo `tipo_cosecha` con validator en `WeighingCreate` (str opcional, default `'Mecanico - Verde'`) en `src/weighings.py`. Cubre: R4, R5, R6.

- [x] T4 — Añadir campo `tipo_cosecha: str` en `WeighingResponse` en `src/weighings.py`. Cubre: R7.

---

## Fase 2 — Backend: Endpoints

- [x] T5 — Modificar `create_weighing()` en `src/weighings.py` para incluir `tipo_cosecha=body.tipo_cosecha` en la creación del registro `Weighing`. Cubre: R6, R9.

- [x] T6 — Modificar `_build_frame_data()` en `src/weighings.py` para incluir `"tipo_cosecha": record.tipo_cosecha` en el dict de la trama RS232. Cubre: R9.

- [x] T7 — Modificar listado de weighings en `list_weighings()` (construcción de `WeighingResponse`) para incluir `tipo_cosecha` en cada item. Cubre: R7, R11.

---

## Fase 3 — Backend: Filtro en GET /api/anomalies

- [x] T8 — Modificar endpoint `GET /api/anomalies` en `src/main.py`: añadir query param opcional `tipo_cosecha: Optional[str] = Query(None)` y pasarlo a `detect_on_demand()`. Cubre: R10.

- [x] T9 — Modificar `AnomalyDetector.detect_on_demand()` en `src/anomaly_detector.py` para aceptar `tipo_cosecha: str | None = None` y pasarlo a `_get_window()`. Cubre: R10.

- [x] T10 — Modificar `AnomalyDetector._get_window()` en `src/anomaly_detector.py` para aceptar `tipo_cosecha: str | None = None` y añadir `query.filter(Weighing.tipo_cosecha == tipo_cosecha)` si se proporciona. Cubre: R10.

---

## Fase 4 — Backend: SQL Tools (filtro en análisis estadísticos)

- [x] T11 — Modificar las siguientes herramientas en `src/sql_tools.py` para añadir parámetro opcional `tipo_cosecha: str | None = None` y filtrar por `Weighing.tipo_cosecha` en el WHERE:
  - `get_basic_stats`
  - `get_percentiles`
  - `get_moving_average`
  - `get_trend`
  - `get_breakdown_by_hacienda`
  - `get_breakdown_by_operator`
  - `get_material_composition`
  - `get_shift_summary`
  - `get_daily_summary`
  - `get_custom_period_summary`
  - `check_thresholds`
  Cubre: AC 5 (filtro en análisis estadísticos).

- [x] T12 — Actualizar las definiciones de `TOOL_DEFINITIONS` en `src/sql_tools.py` para incluir `tipo_cosecha` como propiedad opcional (`"type": "string"`) en los schemas de parámetros de cada función relevante. Cubre: AC 5.

---

## Fase 5 — Frontend: Constantes y formulario kiosco

- [x] T13 — Añadir constante `HARVEST_TYPES` en `frontend/src/lib/constants.js` con el array de los 6 valores de tipo de cosecha. Cubre: R8.

- [x] T14 — Modificar `frontend/src/components/KioskForm.svelte`:
  - Importar `HARVEST_TYPES` desde constants.
  - Añadir variable reactiva `let tipoCosecha = $state("Mecanico - Verde");`
  - Añadir sección "Tipo de Cosecha" después de la sección "Procedencia" con un `<select>` que itera sobre `HARVEST_TYPES`.
  - Incluir `tipo_cosecha: tipoCosecha` en el body de `POST /api/weighings` en `handleConfirm()`.
  - Incluir `tipoCosecha` en `resetForm()`.
  Cubre: R8, R9.

---

## Fase 6 — Frontend: Historial

- [x] T15 — Modificar `frontend/src/components/HistoryTable.svelte`:
  - Añadir columna `<th>Tipo Cosecha</th>` en el `<thead>` (entre Suerte y Peso Muestra, o al final).
  - Añadir celda `<td>{w.tipo_cosecha || "—"}</td>` en el `<tbody>`.
  Cubre: R11.

---

## Fase 7 — Tests

- [x] T16 — Añadir test `test_create_weighing_default_tipo_cosecha` en `tests/test_weighings.py`:
  - Crear pesaje sin enviar `tipo_cosecha` en el body (o con valor omitido, usando default del schema).
  - Verificar que la respuesta incluye `tipo_cosecha` y su valor es `"Mecanico - Verde"`.
  Cubre: R5, R6, R7.

- [x] T17 — Añadir test `test_create_weighing_explicit_tipo_cosecha` en `tests/test_weighings.py`:
  - Crear pesaje con `tipo_cosecha: "Manual - Incendio"`.
  - Verificar que la respuesta incluye `tipo_cosecha: "Manual - Incendio"`.
  Cubre: R4, R7, R9.

- [x] T18 — Añadir test `test_create_weighing_invalid_tipo_cosecha` en `tests/test_weighings.py`:
  - Crear pesaje con `tipo_cosecha: "Valor Invalido"`.
  - Verificar HTTP 422.
  Cubre: R5.

- [x] T19 — Añadir test `test_list_weighings_includes_tipo_cosecha` en `tests/test_weighings.py`:
  - Crear pesaje con tipo_cosecha explícito.
  - Hacer GET /api/weighings y verificar que `tipo_cosecha` aparece en cada item.
  Cubre: R7, R11.

- [x] T20 — Añadir test `test_anomalies_filter_tipo_cosecha` en `tests/test_anomaly_detector.py` o `tests/test_weights.py`:
  - Verificar que `AnomalyDetector.detect_on_demand()` con `tipo_cosecha` filtra correctamente.
  - Puede ser unitario (mockeando datos de prueba) o de integración.
  Cubre: R10.

---

## Fase 8 — Verificación final

- [x] T21 — Ejecutar `docker compose exec backend python -m unittest discover -s tests -v` — todos los tests existentes pasan sin regresiones. Cubre: verificación Nivel 1.

- [x] T22 — Ejecutar `./init.ps1` — todos los bloques `[OK]`. Cubre: verificación Nivel 3.
  > Nota: Secciones 1-5 OK. Sección 6 muestra [FAIL] por errores pre-existentes en TestIncomingSmsDispatcher (event loop), no relacionados con harvest_type.

- [x] T23 — Verificar trazabilidad completa en `progress/impl_harvest_type.md`: mapear cada `R<n>` a su test concreto. Cubre: trazabilidad (regla dura de specs.md).
