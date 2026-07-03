# Tasks — Reset Individual de Pesos en Kiosko de Pesaje

> Feature 24 — reset_individual_pesos
> Pasos en orden, cada uno con R<n> que cubre.

---

## Backend

- [x] T1 — Añadir schema `ResetFieldRequest` con campo opcional `step: Optional[str]` en `src/weighings.py`. Cubre: R4.

- [x] T2 — Modificar `reset_weighing_form()` para aceptar `body: Optional[ResetFieldRequest] = None`. Validar `step` contra valores permitidos. Devolver mensaje específico según el campo. Cubre: R4, R5, R6, R7.

- [x] T3 — Verificar que `POST /api/weighings/reset` sin autenticación retorna HTTP 401 con y sin body. Cubre: R8.

---

## Frontend

- [x] T4 — Añadir prop `onReset` al componente `WeightField.svelte`. Añadir botón "Reset" en la fila de botones (junto a Tara/Leer), que ejecute `onReset` al hacer clic. Cubre: R1, R2.

- [x] T5 — En `KioskForm.svelte`, crear tres manejadores asíncronos (`handleResetPesoMuestra`, `handleResetPesoMineral`, `handleResetPesoVegetal`) que:
  1. Envíen `POST /api/weighings/reset` con `{ step: "<campo>" }` al backend
  2. Establezcan la variable reactiva correspondiente a 0
  Cubre: R1, R2, R4, R5.

- [x] T6 — Pasar `onReset` a cada instancia de `<WeightField>` en el template. Reemplazar la llamada a `handleReset`/`confirmReset` general por los tres manejadores individuales. Cubre: R1, R2.

- [x] T7 — Relegar el botón "Reset general" a acción secundaria:
  - Eliminar el botón del área de acciones primarias (`.form-actions`)
  - Añadir un enlace o botón pequeño "Limpiar todo" en una sección secundaria
  - Mantener el modal de confirmación (`ConfirmModal`) para el reset completo
  Cubre: R3.

---

## Tests

- [x] T8 — Añadir en `tests/test_weighings.py`:
  - `test_reset_individual_step_valid`: POST con `step: "peso_muestra"` → 200 + mensaje específico
  - `test_reset_individual_step_invalid`: POST con `step: "invalido"` → 400
  - `test_reset_individual_without_step`: POST sin body → 200 (backward compat)
  - `test_reset_individual_no_token`: POST con step sin token → 401
  Cubre: R5, R6, R7, R8.

- [x] T9 — Añadir test frontend para `WeightField.svelte` (o `KioskForm.svelte`) que verifique:
  - El botón Reset se renderiza
  - Al hacer clic en Reset, solo ese campo se limpia
  (Crear archivo `frontend/src/components/__tests__/WeightField.test.js`)
  Cubre: R1, R2.
