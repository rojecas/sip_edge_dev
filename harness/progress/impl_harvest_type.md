# Implementación — Feature 18: harvest_type

> Campo tipo de cosecha en registro de pesaje

- **Fecha:** 2026-06-25
- **Agente:** implementer
- **Feature ID:** 18

---

## Archivos creados/modificados

| Archivo | Acción | Descripción |
|---------|--------|-------------|
| `database/migrations/2026_06_25_000001_add_tipo_cosecha_to_weighings.sql` | Creado | Migración SQL: ADD COLUMN tipo_cosecha ENUM |
| `src/models.py` | Modificado | Añadida columna `tipo_cosecha` (ENUM) a clase Weighing + import `text` |
| `src/weighings.py` | Modificado | Añadida const `TIPO_COSECHA_VALUES`, campo `tipo_cosecha` en WeighingCreate (con validator), WeighingResponse, create_weighing(), _build_frame_data(), list_weighings() |
| `src/main.py` | Modificado | Añadido `Query` import, query param `tipo_cosecha` en GET /api/anomalies |
| `src/anomaly_detector.py` | Modificado | `detect_on_demand()` acepta `tipo_cosecha`, `_get_window()` acepta `tipo_cosecha` y filtra |
| `src/sql_tools.py` | Modificado | 11 herramientas SQL aceptan param `tipo_cosecha` + filtrado; TOOL_DEFINITIONS actualizadas |
| `frontend/src/lib/constants.js` | Modificado | Añadida const `HARVEST_TYPES` |
| `frontend/src/components/KioskForm.svelte` | Modificado | Añadido import HARVEST_TYPES, variable tipoCosecha, select en template, inclusión en handleConfirm() y resetForm() |
| `frontend/src/components/HistoryTable.svelte` | Modificado | Añadida columna "Tipo Cosecha" en thead y tbody |
| `tests/test_weighings.py` | Modificado | 4 nuevos tests (T16-T19) |
| `tests/test_anomaly_detector.py` | Modificado | 1 nuevo test (T20) |

---

## Trazabilidad

| Requerimiento | Test |
|--------------|------|
| R1 (Columna tipo_cosecha en BD) | T1 (migración), T2 (modelo), cubierto por los tests de creación/listado que validan el campo |
| R2 (Migración de BD) | T1 (migración SQL) |
| R3 (Modelo ORM Weighing) | T2 (modelo), cubierto por tests que crean/listan weighings |
| R4 (Schema WeighingCreate acepta tipo_cosecha) | `test_create_weighing_explicit_tipo_cosecha` |
| R5 (Validación tipo_cosecha inválido) | `test_create_weighing_invalid_tipo_cosecha`, `test_create_weighing_default_tipo_cosecha` |
| R6 (Default en creación) | `test_create_weighing_default_tipo_cosecha` |
| R7 (WeighingResponse incluye tipo_cosecha) | `test_create_weighing_default_tipo_cosecha`, `test_create_weighing_explicit_tipo_cosecha`, `test_list_weighings_includes_tipo_cosecha` |
| R8 (Select en formulario kiosco) | T13 (HARVEST_TYPES), T14 (KioskForm.svelte) — verificación UI |
| R9 (Persistencia al confirmar) | `test_create_weighing_explicit_tipo_cosecha` |
| R10 (Filtro tipo_cosecha en GET /api/anomalies) | `test_detect_on_demand_filter_tipo_cosecha` |
| R11 (Columna en historial) | `test_list_weighings_includes_tipo_cosecha` |

---

## Decisiones técnicas

1. **Pydantic validator en lugar de Literal:** Se usó `@field_validator` con lista `TIPO_COSECHA_VALUES` en lugar de `typing.Literal`. La lista es reutilizable en frontend y da mensajes de error descriptivos. El frontend usa su propia constante `HARVEST_TYPES` para evitar dependencia del backend.

2. **Filtro en detect_on_demand aplicado directamente:** En lugar de delegar completamente a `_get_window()`, el filtro `tipo_cosecha` se aplica directamente en la query de `detect_on_demand()` ya que `_get_window()` tiene una firma que recibe `db: Session` (usado por `run()`). Se añadió el parámetro opcional `tipo_cosecha` a `_get_window()` para consistencia futura.

3. **Column placement en HistoryTable:** La columna "Tipo Cosecha" se insertó entre "Suerte" y "Peso Muestra" para mantener la jerarquía lógica: metadatos del registro → tipo de cosecha → pesos.

4. **server_default con text():** Para MariaDB, el `server_default` de la columna ENUM usa `text("'Mecanico - Verde'")` para garantizar que el valor por defecto se establezca a nivel de base de datos (las comillas anidadas son necesarias para valores ENUM en SQL).

---

## Impacto en features existentes

### Feature 6 — weighing_capture
- `src/models.py`: Columna nueva en tabla `weighings` → migración añade columna sin afectar datos existentes (valor por defecto)
- `src/weighings.py`: Schemas WeighingCreate/WeighingResponse ampliados con campo opcional → retrocompatible
- Tests: Todos los tests existentes de weighings pasan sin modificaciones ✅

### Feature 8 — ai_agent
- `src/main.py`: Query param opcional `tipo_cosecha` en GET /api/anomalies → retrocompatible (sin parámetro = sin filtro)
- `src/anomaly_detector.py`: `detect_on_demand()` acepta param opcional → retrocompatible
- `src/sql_tools.py`: 11 herramientas ampliadas con param opcional → retrocompatible (execute_tool usa **arguments, ignora params extra)
- Tests: Todos los tests existentes de anomaly_detector y sql_tools pasan ✅

### Feature 13 — frontend_login_kiosk
- `frontend/src/lib/constants.js`: Constante HARVEST_TYPES añadida → sin impacto en imports existentes
- `frontend/src/components/KioskForm.svelte`: Select añadido, body ampliado → sin impacto en funcionalidad existente
- `frontend/src/components/HistoryTable.svelte`: Columna añadida → sin impacto en funcionalidad existente
- Tests: Los componentes no tienen tests unitarios en este proyecto, verificación manual en UI

---

## Verificación

- **Nivel 1 (Tests unitarios):** ✅ 460 tests ejecutados, 5 errores pre-existentes (TestIncomingSmsDispatcher - event loop), 0 regresiones de mis cambios
- **Nivel 3 (init.ps1):** ✅ Secciones 1-5 OK. Sección 6 muestra [FAIL] por los 5 errores pre-existentes en TestIncomingSmsDispatcher (RuntimeError: no current event loop). No relacionados con harvest_type. Todos los tests de harvest_type pasan (5/5 nuevos + 0 regresiones en tests existentes de weighings, anomaly_detector, sql_tools).
- **Nivel 4 (EdgeBox):** No aplica — feature no toca hardware

### Tests nuevos (5/5 OK):
- `test_create_weighing_default_tipo_cosecha` ✅
- `test_create_weighing_explicit_tipo_cosecha` ✅
- `test_create_weighing_invalid_tipo_cosecha` ✅
- `test_list_weighings_includes_tipo_cosecha` ✅
- `test_detect_on_demand_filter_tipo_cosecha` ✅
