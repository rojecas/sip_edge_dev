# Tasks — rs232_resend

> Pasos discretos en orden de ejecución.
>
> **Nota spec-validator (2026-07-23):** Archivo original renombrado a tasks.old.md (ya eliminado).
>
> **Nota líder (2026-07-23):** R5 original eliminado (enviado_pc no es confiable para
> determinar si el PC recibió). T6 ya no verifica `result.enviado_pc` — siempre activa
> `resendMode = true`. T9 ya no incluye test `_stays_if_enviado_pc_true`.
>
> **Nota líder (2026-07-23):** T1 migración corregida a formato `.py` (upgrade/downgrade)
> como F37 y F39. El implementer ejecuta `upgrade()` manualmente en su entorno de
> desarrollo (Docker). El migration tracker automatizado será F45.

---

## Backend

- [x] T1 — Crear migración `database/migrations/2026_07_23_000001_add_resend_count_to_weighings.py`
  con `upgrade()` y `downgrade()`:
  ```python
  def upgrade(connection):
      connection.execute(text("""
          ALTER TABLE weighings
          ADD COLUMN resend_count INTEGER NOT NULL DEFAULT 0
          AFTER enviado_pc
      """))

  def downgrade(connection):
      connection.execute(text("""
          ALTER TABLE weighings
          DROP COLUMN resend_count
      """))
  ```
  **Ejecutar `upgrade()` en el entorno de desarrollo** (Docker: `docker compose exec backend python -c "from database.migrations.2026_07_23_000001_add_resend_count_to_weighings import upgrade; from src.db import engine; upgrade(engine.connect())"` o directamente contra MariaDB).
  Cubre: R6.

- [x] T2 — Agregar columna `resend_count` al modelo `Weighing` en `src/models.py`:
  ```python
  resend_count = Column(Integer, nullable=False, default=0, server_default="0")
  ```
  Cubre: R6.

- [x] T3 — Agregar campo `resend_count: int = Field(default=0)` al schema `WeighingResponse` en `src/weighings.py`.
  Cubre: R5, R7.

- [x] T4 — Implementar endpoint `POST /api/weighings/{id}/resend` en `src/weighings.py`:
  - Buscar registro por `weighing_id` (404 si no existe, 404 si operator ajeno).
  - Construir `frame_data` con `_build_frame_data()`.
  - Llamar a `_send_rs232_frame()`.
  - Incrementar `record.resend_count += 1`.
  - `db.commit()`, `db.refresh(record)`.
  - Retornar `WeighingResponse`.
  - NO ejecutar detección de anomalías.
  Cubre: R2, R3, R5, R7.

## Frontend

- [x] T5 — Agregar `WEIGHINGS_RESEND: "/api/weighings"` en `frontend/src/lib/constants.js`.
  Import requerido: modificar `ENDPOINTS` object.
  Cubre: R1, R2, R8.

- [x] T6 — Modificar `KioskForm.svelte`:
  - Agregar estado reactivo: `lastWeighingId = $state(null)`, `resendMode = $state(false)`.
  - Modificar `handleConfirm()`: tras POST exitoso, guardar `result.id` en `lastWeighingId`, activar `resendMode = true` SIEMPRE (enviado_pc no es confiable — el write al UART puede tener éxito aunque el PC no reciba). NO hacer `resetForm()` ni `setTimeout`.
  - Agregar función `handleResend()` que llama a `POST /api/weighings/{id}/resend`.
  - Agregar función `exitResendMode()` que resetea `resendMode = false` y `lastWeighingId = null`.
  - Bindear `onTara={exitResendMode}` y `onLeer={exitResendMode}` en los 3 `<WeightField>`.
  - Modificar el botón `<button class="btn-confirm">`: condicionar `onclick`, texto y `disabled` según `resendMode`.
  - Llamar `exitResendMode()` en `resetForm()` y `confirmReset()`.
  Cubre: R1, R2, R3, R4.

- [x] T7 — Modificar `HistoryTable.svelte`:
  - Agregar columna `<th>Acción</th>` en el `<thead>`.
  - Importar `authStore`: `import { authStore } from "../stores/auth.js";`.
  - Agregar función `handleResend(weighingId)` que llama a `POST /api/weighings/{id}/resend` y recarga la tabla.
  - En `<tbody>`, agregar `<td>` con botón 🔄 condicionado a `$authStore.isAdmin && !w.enviado_pc`.
  - El botón debe tener `e.stopPropagation()` para no abrir el modal de detalle.
  Cubre: R8, R9.

## Tests

- [x] T8 — Agregar tests backend en `tests/test_weighings.py`:
  - `test_resend_endpoint_returns_200`: llama POST /api/weighings/{id}/resend, verifica status 200.
  - `test_resend_endpoint_increments_resend_count`: verifica que resend_count sube en 1.
  - `test_resend_endpoint_404_if_not_found`: ID inexistente → 404.
  - `test_resend_endpoint_404_if_operator_other_user`: operator intenta reenviar pesaje ajeno → 404.
  - `test_resend_endpoint_does_not_run_anomaly_detection`: verificar que no se invoca `_run_anomaly_detection`.
  - `test_resend_endpoint_updates_enviado_pc`: verificar que enviado_pc se vuelve True si send_frame ok.
  - `test_resend_multiple_times_allowed`: 3 llamadas seguidas, todas 200, resend_count=3.
  - `test_resend_count_defaults_to_zero_on_create`: crear pesaje, verificar resend_count=0.
  Cubre: R2, R3, R5, R6, R7.

- [x] T9 — Agregar tests frontend (en `frontend/src/components/KioskForm.test.js` o similar):
  - `test_confirm_button_changes_to_resend_after_post`: mock POST /api/weighings → 201, verificar texto botón cambia a "Reenviar Datos" siempre (sin importar enviado_pc).
  - `test_resend_button_triggers_api_call`: click Reenviar Datos, verificar llamada a POST /api/weighings/{id}/resend.
  - `test_resend_mode_exits_on_tara_or_leer`: tras activar resendMode, simular Tara/Leer, verificar botón vuelve a Confirmar.
  Cubre: R1, R2, R4.

- [x] T10 — Agregar tests frontend en `HistoryTable.test.js` (o similar):
  - `test_admin_history_resend_button_visible`: mock authStore.isAdmin=true, verificar botón 🔄 presente en fila con enviado_pc=false.
  - `test_operator_history_resend_button_not_visible`: mock authStore.isAdmin=false, verificar botón 🔄 ausente.
  - `test_resend_button_not_shown_if_enviado_pc_true`: verificar botón 🔄 ausente en fila con enviado_pc=true.
  Cubre: R8, R9.
