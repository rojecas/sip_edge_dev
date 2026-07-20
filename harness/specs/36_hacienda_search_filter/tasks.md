# Tasks — Feature 36: Entrada de Código de Hacienda en Kiosko y AdminSuertes

> Checkbox ejecutable. El implementer marca `[x]` al completar cada paso.
> Cada task referencia al menos un `R<n>` que cubre.

---

## Backend

- [x] T1 — Agregar parámetro `search: Optional[str] = Query(None)` al endpoint `GET /api/haciendas` en `src/haciendas.py`. Aplicar filtro case-insensitive `func.lower(Hacienda.codigo) == search.lower()` cuando el parámetro está presente. Cubre: **R4**.
- [x] T2 — Agregar test `test_list_haciendas_search_found` en `tests/test_haciendas.py`: crear hacienda con código conocido, buscar con `?search=<codigo>&page_size=1`, verificar que retorna 1 item en `items`. Cubre: **R3, R4**.
- [x] T3 — Agregar test `test_list_haciendas_search_not_found` en `tests/test_haciendas.py`: buscar con un código inexistente, verificar `items` vacío y `total=0`. Cubre: **R7**.
- [x] T4 — Agregar test `test_list_haciendas_search_case_insensitive` en `tests/test_haciendas.py`: verificar que el filtro es case-insensitive — código "a16" matchea "A16" y viceversa. Cubre: **R4**.
- [x] T5 — Agregar test `test_list_haciendas_search_backward_compatible` en `tests/test_haciendas.py`: llamar a `GET /api/haciendas` sin parámetro `search` y verificar que la respuesta paginada sigue siendo correcta (todos los items). Cubre: **R4** (retrocompatibilidad).

## Frontend — Componente compartido

- [x] T6 — Crear `frontend/src/components/HaciendaCodeInput.svelte` con:
  - Estado interno: `inputValue`, `selectedHacienda`, `showErrorModal`, `searchCode`, `loading`.
  - Props: `onSelect(hacienda | null)`, `placeholder`.
  - Formato de display fijo: `CODIGO - NOMBRE` (sin prop `format`).
  - **Subtask:** importar `onMount` de `svelte`.
  - **Subtask:** importar `api`, `buildQuery` de `../lib/api.js`.
  - **Subtask:** importar `ENDPOINTS` de `../lib/constants.js`.
  Cubre: **R11**.

- [x] T7 — Implementar lógica de búsqueda en `HaciendaCodeInput.svelte`:
  - Al presionar Enter o Tab, disparar `GET /api/haciendas?search=<valor>&page_size=1`.
  - NO disparar llamadas en cada keystroke (solo Enter/Tab).
  - Manejar loading state mientras se resuelve la API.
  Cubre: **R3**.

- [x] T8 — Implementar display confirmado en `HaciendaCodeInput.svelte`:
  - Mostrar siempre el formato `CODIGO - NOMBRE` (ej. `131 - Hacienda San José`).
  - Mostrar botón limpiar (`x`) junto al texto confirmado.
  - Al presionar `x`: llamar `onSelect(null)`, resetear `inputValue`, `selectedHacienda`.
  Cubre: **R5, R6**.

- [x] T9 — Implementar modal de error en `HaciendaCodeInput.svelte`:
  - Mensaje: "El código 'XXX' no corresponde a ninguna hacienda registrada."
  - Explicación: "Esto puede deberse a un error de digitación o a una hacienda nueva que aún no ha sido creada."
  - Botón **[Reintentar]**: cierra modal, enfoca el campo de texto.
  - Botón **[Crear nueva hacienda]**: navega a `/#/kiosco/haciendas`.
  Cubre: **R7, R8, R9**.

- [x] T10 — Implementar reseteo de suertes en `HaciendaCodeInput.svelte`:
  - El callback `onSelect(null)` DEBE ser invocado al limpiar.
  - El consumidor (KioskForm/AdminSuertes) DEBE vaciar las suertes al recibir `onSelect(null)`.
  Cubre: **R10**.

## Frontend — Integración en KioskForm

- [x] T11 — Modificar `frontend/src/components/KioskForm.svelte`:
  - Reemplazar el bloque `<select>` de hacienda (líneas 314–333) por `<HaciendaCodeInput>`.
  - Eliminar variables `haciendas`, `haciendasLoading`, `haciendasError`.
  - Eliminar funciones `loadHaciendas()`, `loadRemainingHaciendas()`.
  - Conectar `onSelect` para actualizar `selectedHaciendaId`.
  - **Subtask:** importar `HaciendaCodeInput` de `./HaciendaCodeInput.svelte`.
  Cubre: **R1, R5, R11**.

- [x] T12 — Verificar que `isFormValid()` en KioskForm sigue funcionando:
  `selectedHaciendaId !== null && selectedHaciendaId !== undefined`.
  Cubre: **R1**.

## Frontend — Integración en AdminSuertes

- [x] T13 — Modificar `frontend/src/components/AdminSuertes.svelte`:
  - Reemplazar el `<select>` de hacienda (líneas 227–236) por `<HaciendaCodeInput>`.
  - Eliminar variables `haciendas`, `haciendasLoading`.
  - Eliminar funciones `loadHaciendas()`, `loadRemainingHaciendas()`.
  - Conectar `onSelect` para actualizar `selectedHaciendaId`.
  - **Subtask:** importar `HaciendaCodeInput` de `./HaciendaCodeInput.svelte`.
  Cubre: **R2, R5, R11**.

- [x] T14 — Verificar que el `$effect` reactivo de `selectedHaciendaId` en AdminSuertes sigue cargando suertes al cambiar la hacienda seleccionada. Cubre: **R2, R10**.

## Tests de frontend

- [x] T15 — Agregar test `test_hacienda_code_input_found` (en archivo de test apropiado, ej. `HaciendaCodeInput.test.js`): simular entrada de código existente y Enter, verificar display confirmado con formato `CODIGO - NOMBRE`. Cubre: **R3, R5**.
- [x] T16 — Agregar test `test_hacienda_code_input_not_found` en `HaciendaCodeInput.test.js`: simular código inexistente, verificar modal de error con texto correcto y botones. Cubre: **R7, R8, R9**.
- [x] T17 — Agregar test `test_hacienda_code_input_clear` en `HaciendaCodeInput.test.js`: simular selección confirmada, presionar botón limpiar, verificar que `onSelect(null)` se invoca. Cubre: **R6, R10**.
- [x] T18 — Agregar test `test_hacienda_code_input_no_keystroke_calls` en `HaciendaCodeInput.test.js`: simular escritura de 5 caracteres sin Enter/Tab, verificar que NO hay llamadas a la API. Cubre: **R3**.
