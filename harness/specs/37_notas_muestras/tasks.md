# Tasks — Feature 37: notas_muestras

> Pasos discretos en orden de implementación.
> Cada task referencia al menos un R<n>.
> Aprobación humana 2026-07-20: T16/T17 reemplazados — columna en tabla → modal de detalle (WeighingDetailModal).

---

## Fase 1 — Backend: Migración y Modelo

- [x] T1 — Crear migración `database/migrations/2026_07_20_000001_add_notas_to_weighings.py` con `ALTER TABLE weighings ADD COLUMN notas TEXT NULL AFTER tipo_cosecha`. Cubre: R1.
- [x] T2 — Agregar columna `notas = Column(Text, nullable=True, default=None)` en la clase `Weighing` de `src/models.py`. Cubre: R1.

## Fase 2 — Backend: Schema y Endpoint

- [x] T3 — Agregar `notas: Optional[str] = Field(default=None, max_length=65535)` en `WeighingCreate` en `src/weighings.py`. Agregar `field_validator` que normalice cadena vacía a `None` para cubrir R11 en llamadas API directas. Cubre: R5, R11.
- [x] T4 — Agregar `notas: Optional[str] = None` en `WeighingResponse` en `src/weighings.py`. Cubre: R12.
- [x] T5a — Modificar `create_weighing()` en `src/weighings.py` para pasar `notas=body.notas` al constructor de `Weighing`. Cubre: R5, R11.
- [x] T5b — **CRÍTICO:** Modificar `list_weighings()` en `src/weighings.py` para agregar `notas=w.notas` en la construcción manual de `WeighingResponse` (líneas 263-280). Sin este cambio, `GET /api/weighings` no retornará el campo `notas`. Cubre: R7, R12.
- [x] T6 — Agregar `"notas": record.notas` en `_build_frame_data()` en `src/weighings.py` (paso preparatorio para incluir notas en la trama RS232). NOTA: el dict se pasa a `send_frame()` en `src/rs232.py`, pero `send_frame` construye la línea CSV con claves explícitas. Para que `notas` aparezca realmente en la trama RS232, se requiere un segundo paso: modificar `src/rs232.py:send_frame()` para incluir `frame_data.get('notas', '')` al final de `csv_line` (requiere coordinación con equipo PC externo — Feature 11). Este task solo cubre el paso preparatorio. Cubre: R5 (preparación).

## Fase 3 — Backend: Tool SQL para agente AI

- [x] T7 — Agregar entrada `get_weighing_notes` en `TOOL_DEFINITIONS` en `src/sql_tools.py` con parámetros `vagon`, `fecha_inicio`, `fecha_fin`, `limit`. Cubre: R9.
- [x] T8 — Implementar método `get_weighing_notes()` en clase `SqlTools` en `src/sql_tools.py` que consulte `weighings.notas` con filtros opcionales por vagon y rango de fechas. Cubre: R9, R10.
- [x] T9 — Registrar `get_weighing_notes` en el diccionario `tool_map` del método `execute_tool()` en `src/sql_tools.py`. Cubre: R9.

## Fase 4 — Frontend: Componente colapsable NotesField

- [x] T10 — Crear `frontend/src/components/NotesField.svelte`:
  - Input: `bind:notas`, `label` (prop).
  - Estado `expanded` con toggle via botón + icono de expandir/colapsar.
  - Área de texto `<textarea>` con mínimo 3 líneas de altura cuando expandido.
  - Indicador de estado colapsado: muestra "Notas" + resumen de texto si hay contenido.
  - Animación CSS suave de transición de altura.
  - Subtask: importar `$state` de Svelte.
  Cubre: R2, R3, R4.

## Fase 5 — Frontend: Integración en KioskForm

- [x] T11 — Importar `NotesField` en `KioskForm.svelte`. Cubre: R2.
- [x] T12 — Agregar estado `let notas = $state("");` en el `<script>` de `KioskForm.svelte`. Cubre: R2.
- [x] T13 — Insertar `<NotesField bind:notas={notas} />` en el template de `KioskForm.svelte`, debajo de la sección de pesos. Cubre: R2.
- [x] T14 — Agregar `notas: notas || null` en el body de `handleConfirm()` en `KioskForm.svelte` para enviar notas en POST `/api/weighings`. Cubre: R5, R11.
- [x] T15 — Agregar `notas = "";` en la función `resetForm()` de `KioskForm.svelte` para limpiar notas al resetear el formulario. Cubre: R6.

## Fase 6 — Frontend: Modal de detalle en historial

- [x] T16 — Crear `frontend/src/components/WeighingDetailModal.svelte`:
  - Props: `weighing` (objeto completo del pesaje), `onclose` (callback).
  - Overlay semitransparente + panel centrado con layout de detalle.
  - Layout de dos columnas (etiqueta: valor) para todos los campos: Fecha, Hora, Tractomula, Vagón, Guía, Hacienda, Suerte, Tipo Cosecha.
  - Sección de pesos: Muestra, Mineral, Vegetal con formato 3 decimales.
  - Sección de notas al pie del modal: texto completo si existe, "Sin observaciones" si es NULL/vacío.
  - Cierre: botón X, tecla Escape (`onkeydown` en `svelte:window`), click en overlay (no en panel).
  - Subtask: importar `onMount`, `onDestroy` de Svelte para registrar/limpiar listener de teclado.
  Cubre: R7, R8.

- [x] T17 — Modificar `HistoryTable.svelte`:
  - Importar `WeighingDetailModal`.
  - Agregar estado `let selectedWeighing = $state(null);` y `let showDetail = $state(false);`.
  - Agregar `onclick={() => { selectedWeighing = w; showDetail = true; }}` en cada `<tr>` del `<tbody>`.
  - Agregar `cursor: pointer` en el CSS de `.data-table tbody tr`.
  - Renderizar condicionalmente: `{#if showDetail && selectedWeighing}` → `<WeighingDetailModal weighing={selectedWeighing} onclose={() => showDetail = false} />`.
  Cubre: R7.

## Fase 7 — Tests Backend

- [x] T18 — Agregar test `test_create_weighing_with_notes` en `tests/test_weighings.py` que verifique que POST `/api/weighings` con `notas` persiste y retorna el campo en la respuesta. Cubre: R5, R12.
- [x] T19 — Agregar test `test_create_weighing_without_notes_null` en `tests/test_weighings.py` que verifique que POST `/api/weighings` sin `notas` persiste `null`. Cubre: R11.
- [x] T20a — Agregar test `test_create_weighing_with_empty_notes` en `tests/test_weighings.py` que verifique que POST `/api/weighings` con `notas: ""` persiste `null` (vía field_validator en T3). Cubre: R11.
- [x] T20b — Agregar test `test_create_weighing_with_long_notes` en `tests/test_weighings.py` que verifique que POST `/api/weighings` con un texto de >1000 caracteres persiste y retorna el texto completo sin truncamiento. Cubre: R13.
- [x] T21 — Agregar test `test_list_weighings_includes_notes` en `tests/test_weighings.py` que verifique que GET `/api/weighings` incluye campo `notas` en los items. Cubre: R7, R12.
- [x] T22 — Agregar test `test_get_weighing_notes_tool_by_vagon` en `tests/test_sql_tools.py` que verifique que `get_weighing_notes(vagon="VAG-001")` retorna notas del vagon especificado. Cubre: R9.
- [x] T23 — Agregar test `test_get_weighing_notes_tool_by_date_range` en `tests/test_sql_tools.py` que verifique que `get_weighing_notes(fecha_inicio="2026-07-01", fecha_fin="2026-07-20")` retorna notas en el rango. Cubre: R9.
- [x] T24 — Agregar test `test_get_weighing_notes_tool_no_params_error` en `tests/test_sql_tools.py` que verifique que la tool lanza `ToolExecutionError` si no se proporciona ni vagon ni rango de fechas. Cubre: R9.

## Fase 8 — Tests Frontend

- [x] T25 — Agregar test en `frontend/src/components/__tests__/KioskForm.test.js` que verifique que el campo de notas colapsable se renderiza en el formulario. Cubre: R2.
- [x] T26 — Agregar test en `frontend/src/components/__tests__/KioskForm.test.js` que verifique que al hacer clic en expandir se muestra el textarea y al colapsar se oculta. Cubre: R3, R4.
- [x] T27 — Agregar test en `frontend/src/components/__tests__/KioskForm.test.js` que verifique que al resetear el formulario el campo notas se limpia. Cubre: R6.
- [x] T28 — Agregar test en `frontend/src/components/__tests__/HistoryTable.test.js` que verifique que al hacer click en una fila se abre el modal con las notas del pesaje. Cubre: R7.
- [x] T29 — Agregar test en `frontend/src/components/__tests__/HistoryTable.test.js` que verifique que el modal muestra "Sin observaciones" cuando el pesaje no tiene notas. Cubre: R8.
