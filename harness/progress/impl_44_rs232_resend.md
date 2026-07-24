# Implementación — F44 rs232_resend

## Skills consultados

- `svelte5` — Reglas duras para Svelte 5 (runes, stores, onMount, component API)
- `test-driven-development` — TDD cycle: RED → GREEN → REFACTOR

## Resumen de lo implementado

Feature de reenvío de datos RS232 desde el kiosko. Permite al operador reenviar la trama RS232
de un pesaje ya registrado, y al administrador reenviar cualquier pesaje desde el historial.

### Backend

1. **Migración:** Nueva columna `resend_count INTEGER NOT NULL DEFAULT 0` en tabla `weighings`.
   Archivo: `database/migrations/2026_07_23_000001_add_resend_count_to_weighings.py`.
   Ejecutada contra MariaDB en Docker.

2. **Modelo:** Agregada columna `resend_count` a la clase `Weighing` en `src/models.py`.

3. **Schema:** Agregado campo `resend_count: int = Field(default=0)` en `WeighingResponse` (Pydantic).

4. **Endpoint:** `POST /api/weighings/{id}/resend` en `src/weighings.py`:
   - Busca el registro por ID.
   - Operador solo puede reenviar sus propios registros (404 si ajeno).
   - Carga Hacienda y Suerte asociadas.
   - Construye trama con `_build_frame_data()`.
   - Transmite con `_send_rs232_frame()`.
   - Incrementa `resend_count += 1`.
   - NO ejecuta detección de anomalías.
   - Retorna `WeighingResponse` con HTTP 200.

5. **Listado:** Actualizado `list_weighings` para incluir `resend_count` en los items.

### Frontend

6. **Constante:** Agregado `WEIGHINGS_RESEND: "/api/weighings"` en `constants.js`.

7. **KioskForm.svelte:**
   - Estados reactivos: `lastWeighingId`, `resendMode`.
   - `handleConfirm()`: tras POST exitoso, guarda `result.id` y activa `resendMode = true`
     SIEMPRE (R1 — enviado_pc no es confiable).
   - `handleResend()`: llama a `POST /api/weighings/{id}/resend`.
   - `exitResendMode()`: resetea `resendMode = false`, `lastWeighingId = null`.
   - Botón condicional: "Confirmar Medidas" ↔ "Reenviar Datos" según `resendMode`.
   - `onTara`/`onLeer` en los 3 WeightField llaman a `exitResendMode()`.
   - `resetForm()` y `confirmReset()` llaman a `exitResendMode()`.

8. **HistoryTable.svelte:**
   - Importado `authStore`.
   - Nueva columna "Acción" en `<thead>` y `<tbody>`.
   - Botón 🔄 en cada fila, visible solo para admin (`$authStore.isAdmin`) cuando
     `!w.enviado_pc`.
   - `e.stopPropagation()` en el botón para no abrir el modal de detalle.
   - CSS para `.btn-action`.

## Trazabilidad R<n> → test

| R   | Test                                                                 | Archivo                    |
|-----|----------------------------------------------------------------------|----------------------------|
| R1  | `test_resend_endpoint_returns_200`                                   | tests/test_weighings.py    |
| R2  | `test_resend_endpoint_returns_200`, `test_resend_endpoint_updates_enviado_pc` | tests/test_weighings.py |
| R3  | `test_resend_multiple_times_allowed`                                 | tests/test_weighings.py    |
| R4  | `test_resend_count_defaults_to_zero_on_create` (verifica estructura inicial) | tests/test_weighings.py |
| R5  | `test_resend_endpoint_returns_200`, `test_resend_endpoint_404_if_not_found`, `test_resend_endpoint_404_if_operator_other_user`, `test_resend_endpoint_updates_enviado_pc` | tests/test_weighings.py |
| R6  | `test_resend_count_defaults_to_zero_on_create`                       | tests/test_weighings.py    |
| R7  | `test_resend_endpoint_increments_resend_count`                       | tests/test_weighings.py    |
| R8  | `muestra boton de reenvio para admin cuando enviado_pc es false`     | HistoryTable.test.js       |
| R9  | `no muestra boton de reenvio para operador`                          | HistoryTable.test.js       |

### Verificación adicional

- `test_resend_endpoint_does_not_run_anomaly_detection` — verifica que NO se ejecuta detección de anomalías en reenvío.

## Tasks completadas

- [x] T1 — Migración ejecutada en BD de desarrollo
- [x] T2 — Columna `resend_count` en modelo `Weighing`
- [x] T3 — Campo `resend_count` en schema `WeighingResponse`
- [x] T4 — Endpoint `POST /api/weighings/{id}/resend`
- [x] T5 — Constante `WEIGHINGS_RESEND` en `constants.js`
- [x] T6 — KioskForm.svelte con lógica de reenvío
- [x] T7 — HistoryTable.svelte con botón admin 🔄
- [x] T8 — 8 tests backend en `test_weighings.py` (49 tests total, todos OK)
- [x] T9 — 3 tests frontend KioskForm (KioskForm.test.js) — Nota: 7 tests pre-existentes fallan por mock `emergencyStore.subscribe`, no relacionados con esta feature
- [x] T10 — 2 tests frontend HistoryTable (HistoryTable.test.js) — 4 tests total, todos OK

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `database/migrations/2026_07_23_000001_add_resend_count_to_weighings.py` | NUEVO — migración |
| `src/models.py` | Agregada columna `resend_count` |
| `src/weighings.py` | Agregado endpoint `/resend`, campo schema, listado |
| `tests/test_weighings.py` | 8 nuevos tests (clase `TestWeighingsResend`) |
| `frontend/src/lib/constants.js` | Agregado `WEIGHINGS_RESEND` |
| `frontend/src/components/KioskForm.svelte` | Lógica resendMode + botón condicional |
| `frontend/src/components/HistoryTable.svelte` | Columna Acción + botón 🔄 admin-only |
| `frontend/src/components/__tests__/KioskForm.test.js` | 3 nuevos tests Feature 44 |
| `frontend/src/components/__tests__/HistoryTable.test.js` | 2 nuevos tests Feature 44 + mock authStore |
| `frontend/dist/` | Build recompilado |
| `src/static/` | Frontend copiado |

## Impacto en features existentes

- **F6 (weighing_capture):** Schema `WeighingResponse` actualizado con `resend_count`. Compatibilidad hacia atrás total (campo nuevo con default).
- **F11 (rs232_transmission):** Sin impacto. `_send_rs232_frame()` reutilizado sin modificar.
- **F13 (frontend_login_kiosk):** Sin impacto. KioskForm modificado pero APIs no cambian.
- **F37 (notas_muestras):** Sin impacto. El listado ya incluía `notas`, ahora también incluye `resend_count`.
