<script>
  /**
   * AdminSuertes — Suerte management: filter by hacienda, list, create, edit, delete.
   */
  import { api, ApiError, buildQuery } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";
  import ConfirmModal from "./ConfirmModal.svelte";
  import SuerteFormModal from "./SuerteFormModal.svelte";
  import HaciendaCodeInput from "./HaciendaCodeInput.svelte";

  let { allowDelete = true } = $props();

  // Selected hacienda (id set via HaciendaCodeInput.onSelect)
  let selectedHaciendaId = $state(0);
  // Haciendas array (minimal — populated from selection, for SuerteFormModal compatibility)
  let haciendas = $state([]);

  // Suertes list
  let suertes = $state([]);
  let suertesLoading = $state(false);
  let suertesError = $state("");
  let emptyMsg = $state("");

  // Result messages
  let resultMsg = $state("");
  let resultError = $state(false);

  // Delete confirm
  let confirmShow = $state(false);
  let confirmTarget = $state(null);

  // Form modal
  let formShow = $state(false);
  let formMode = $state("create");
  let formSuerte = $state(null);
  let formHaciendaId = $state(0);
  let formError = $state("");
  let formSubmitting = $state(false);

  // Pagination state
  let currentPage = $state(1);
  let totalPages = $state(1);
  let totalItems = $state(0);
  let pageSize = $state(10);

  // Reactively load suertes when selectedHaciendaId changes
  $effect(() => {
    if (selectedHaciendaId) {
      currentPage = 1;
      loadSuertes();
    } else {
      suertes = [];
      emptyMsg = '';
    }
  });

  /**
   * Handle hacienda selection from HaciendaCodeInput (R2).
   * Called with hacienda object on confirm, or null on clear.
   */
  function handleHaciendaSelect(hacienda) {
    if (hacienda) {
      selectedHaciendaId = hacienda.id;
      haciendas = [hacienda];  // keep minimal array for SuerteFormModal compatibility
    } else {
      selectedHaciendaId = 0;
      haciendas = [];
    }
  }

  async function loadSuertes() {
    if (!selectedHaciendaId) {
      suertes = [];
      return;
    }
    suertesLoading = true;
    suertesError = "";
    emptyMsg = "";
    try {
      const qs = buildQuery({ hacienda_id: selectedHaciendaId });
      const result = await api.get(`${ENDPOINTS.SUERTES}${qs}`);
      suertes = Array.isArray(result) ? result : (result.items || []);
      if (!suertes || suertes.length === 0) {
        emptyMsg = "No hay suertes registradas para esta hacienda.";
        suertes = [];
      }
    } catch (err) {
      suertesError = err instanceof ApiError ? err.message : "Error de conexión.";
    } finally {
      suertesLoading = false;
    }
  }

function showResult(msg, isError = false) {
    resultMsg = msg;
    resultError = isError;
    if (!isError) setTimeout(() => { resultMsg = ""; }, 3000);
  }

  function openCreate() {
    formMode = "create";
    formSuerte = null;
    formHaciendaId = selectedHaciendaId;
    formError = "";
    formSubmitting = false;
    formShow = true;
  }

  function openEdit(s) {
    formMode = "edit";
    formSuerte = s;
    formHaciendaId = s.hacienda_id;
    formError = "";
    formSubmitting = false;
    formShow = true;
  }

  async function handleFormSave(payload) {
    formSubmitting = true;
    formError = "";
    try {
      if (formMode === "create") {
        await api.post(ENDPOINTS.SUERTES, payload);
        formShow = false;
        await loadSuertes();
        showResult("Suerte creada exitosamente.");
      } else {
        await api.put(`${ENDPOINTS.SUERTES_BY_ID}${formSuerte.id}`, payload);
        formShow = false;
        await loadSuertes();
        showResult("Suerte actualizada exitosamente.");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 409) {
          formError = err.message;
          // Modal stays open to let the user correct the duplicate code
        } else {
          formError = err.message;
        }
      } else {
        formError = "Error de conexión.";
      }
    } finally {
      formSubmitting = false;
    }
  }

  function closeForm() {
    formShow = false;
  }

  function openDelete(s) {
    confirmTarget = s;
    confirmShow = true;
  }

  async function confirmDelete() {
    if (!confirmTarget) return;
    try {
      await api.del(`${ENDPOINTS.SUERTES_BY_ID}${confirmTarget.id}`);
      confirmShow = false;
      confirmTarget = null;
      await loadSuertes();
      showResult("Suerte eliminada exitosamente.");
    } catch (err) {
      confirmShow = false;
      showResult(err instanceof ApiError ? err.message : "Error de conexión.", true);
    }
  }

  function goToPage(page) {
    currentPage = page;
    loadSuertes();
  }

  function changePageSize(e) {
    pageSize = parseInt(e.target.value);
    currentPage = 1;
    loadSuertes();
  }

  function cancelDelete() {
    confirmShow = false;
    confirmTarget = null;
  }

  function formatDate(dateStr) {
    if (!dateStr) return "—";
    try {
      return new Date(dateStr).toLocaleString("es-CO", {
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  }
</script>

<div class="suertes-page">
  <div class="page-header">
    <h1>Suertes</h1>
  </div>

  <!-- Hacienda selector -->
  <div class="selector-row">
    <label>
      Hacienda:
      <HaciendaCodeInput onSelect={handleHaciendaSelect} placeholder="Ingrese código de hacienda" />
    </label>
  </div>

  {#if resultMsg}
    <div class="result-banner" class:result-error={resultError}>{resultMsg}</div>
  {/if}

  {#if !selectedHaciendaId}
    <div class="empty-box">
      <span class="empty-icon">🌱</span>
      <p>Seleccione una hacienda para ver sus suertes</p>
    </div>
  {:else if suertesLoading}
    <div class="loading">Cargando suertes...</div>
  {:else if suertesError}
    <div class="error-box">
      <p>{suertesError}</p>
      <button class="btn btn-secondary" onclick={loadSuertes}>Reintentar</button>
    </div>
  {:else if emptyMsg}
    <div class="empty-box">
      <span class="empty-icon">📋</span>
      <p>{emptyMsg}</p>
      <button class="btn btn-primary" onclick={openCreate}>+ Nueva Suerte</button>
    </div>
  {:else}
    <div class="table-header">
      <button class="btn btn-primary" onclick={openCreate}>+ Nueva Suerte</button>
    </div>
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Código Suerte</th>
            <th>Creado</th>
            <th>Actualizado</th>
            <th>Creado por</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each suertes as s}
            <tr>
              <td>{s.codigo_suerte || "—"}</td>
              <td>{formatDate(s.created_at)}</td>
              <td>{formatDate(s.updated_at)}</td>
              <td>{s.created_by_username || "—"}</td>
              <td class="actions-cell">
                <button class="btn-action" onclick={() => openEdit(s)} title="Editar">✏️</button>
                {#if allowDelete}
                  <button class="btn-action" onclick={() => openDelete(s)} title="Eliminar">🗑️</button>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
      {#if totalPages > 1}
        <div class="pagination">
          <button class="btn-page" disabled={currentPage <= 1} onclick={() => goToPage(currentPage - 1)}>Anterior</button>
          <span class="page-info">
            <select class="page-size-select" value={pageSize} onchange={changePageSize}>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
            Página {currentPage} de {totalPages}
          </span>
          <button class="btn-page" disabled={currentPage >= totalPages} onclick={() => goToPage(currentPage + 1)}>Siguiente</button>
        </div>
      {/if}
    </div>
  {/if}
</div>

<SuerteFormModal
  show={formShow}
  mode={formMode}
  suerte={formSuerte}
  haciendaId={formHaciendaId}
  haciendas={haciendas}
  error={formError}
  onClose={closeForm}
  onSave={handleFormSave}
/>

<ConfirmModal
  show={confirmShow}
  title="Eliminar Suerte"
  message={confirmTarget ? `¿Está seguro de eliminar la suerte ${confirmTarget.codigo_suerte}?` : ""}
  confirmText="Eliminar"
  cancelText="Cancelar"
  onConfirm={confirmDelete}
  onCancel={cancelDelete}
/>

<style>
  .suertes-page { max-width: 1000px; }
  .page-header { margin-bottom: 24px; }
  .page-header h1 { font-size: 24px; }
  .selector-row { margin-bottom: 24px; }
  .selector-row label { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--text-secondary); max-width: 360px; }
  .result-banner {
    padding: 12px 18px; border-radius: 8px; font-size: 14px; font-weight: 500;
    margin-bottom: 16px;
    background: rgba(81, 207, 102, 0.1); color: var(--success);
    border: 1px solid var(--success);
  }
  .result-error { background: rgba(255, 107, 107, 0.1); color: var(--error); border-color: var(--error); }
  .loading { color: var(--text-secondary); font-size: 15px; padding: 24px 0; }
  .error-box { text-align: center; padding: 40px 0; color: var(--error); }
  .empty-box { text-align: center; padding: 60px 0; color: var(--text-secondary); }
  .empty-icon { font-size: 48px; display: block; margin-bottom: 12px; opacity: 0.4; }
  .table-header { display: flex; justify-content: flex-end; margin-bottom: 12px; }
  .table-wrapper { overflow-x: auto; border: 1px solid var(--border); border-radius: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 12px 16px; background: var(--bg-secondary); color: var(--text-secondary); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
  td { padding: 10px 16px; border-bottom: 1px solid var(--border); color: var(--text-primary); white-space: nowrap; }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr:hover { background: rgba(255, 255, 255, 0.02); }
  .actions-cell { display: flex; gap: 6px; }
  .btn { padding: 10px 20px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
  .btn-primary { background: var(--accent); color: white; }
  .btn-primary:hover { background: var(--accent-hover); }
  .btn-secondary { background: var(--bg-input); color: var(--text-primary); border: 1px solid var(--border); }
  .btn-secondary:hover { background: var(--border); }
  .btn-action { background: none; border: none; cursor: pointer; font-size: 16px; padding: 4px 6px; border-radius: 4px; transition: background 0.2s; }
  .btn-action:hover { background: var(--bg-input); }
</style>
