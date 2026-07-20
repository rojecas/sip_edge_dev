<script>
  /**
   * AdminHaciendas — Hacienda management: list, create, edit, delete (soft-delete).
   */
  import { api, ApiError, buildQuery } from "../lib/api.js";
  import { onMount } from "svelte";
  import { ENDPOINTS, CONFIG } from "../lib/constants.js";
  import ConfirmModal from "./ConfirmModal.svelte";
  import HaciendaFormModal from "./HaciendaFormModal.svelte";

  let { allowDelete = true } = $props();

  let haciendas = $state([]);
  let loading = $state(true);
  let loadError = $state("");
  let emptyMsg = $state("");
  let currentPage = $state(1);
  let totalPages = $state(1);
  let totalItems = $state(0);
  let pageSize = $state(10);

  let resultMsg = $state("");
  let resultError = $state(false);

  // Delete confirm
  let confirmShow = $state(false);
  let confirmTarget = $state(null);

  // Form modal
  let formShow = $state(false);
  let formMode = $state("create");
  let formHacienda = $state(null);
  let formError = $state("");
  let formSubmitting = $state(false);

  onMount(() => { loadHaciendas(); });

  async function loadHaciendas() {
    loading = true;
    loadError = "";
    emptyMsg = "";
    try {
      const qs = buildQuery({
        page: currentPage,
        page_size: pageSize,
        sort_by: "nombre",
        sort_order: "asc",
      });
      const result = await api.get(`${ENDPOINTS.HACIENDAS}${qs}`);
      haciendas = result.items || [];
      totalPages = result.total_pages || 1;
      totalItems = result.total || 0;
      if (!haciendas || haciendas.length === 0) {
        emptyMsg = "No hay haciendas registradas.";
        haciendas = [];
      }
    } catch (err) {
      loadError = err instanceof ApiError ? err.message : "Error de conexión. Verifique que el servidor esté disponible.";
    } finally {
      loading = false;
    }
  }

  function showResult(msg, isError = false) {
    resultMsg = msg;
    resultError = isError;
    if (!isError) setTimeout(() => { resultMsg = ""; }, 3000);
  }

  function openCreate() {
    formMode = "create";
    formHacienda = null;
    formError = "";
    formSubmitting = false;
    formShow = true;
  }

  function openEdit(h) {
    formMode = "edit";
    formHacienda = h;
    formError = "";
    formSubmitting = false;
    formShow = true;
  }

  async function handleFormSave(payload) {
    formSubmitting = true;
    formError = "";
    try {
      if (formMode === "create") {
        await api.post(ENDPOINTS.HACIENDAS, payload);
        formShow = false;
        await loadHaciendas();
        showResult("Hacienda creada exitosamente.");
      } else {
        await api.put(`${ENDPOINTS.HACIENDAS_BY_ID}${formHacienda.id}`, payload);
        formShow = false;
        await loadHaciendas();
        showResult("Hacienda actualizada exitosamente.");
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

  function openDelete(h) {
    confirmTarget = h;
    confirmShow = true;
  }

  async function confirmDelete() {
    if (!confirmTarget) return;
    try {
      await api.del(`${ENDPOINTS.HACIENDAS_BY_ID}${confirmTarget.id}`);
      confirmShow = false;
      confirmTarget = null;
      await loadHaciendas();
      showResult("Hacienda eliminada exitosamente.");
    } catch (err) {
      confirmShow = false;
      showResult(err instanceof ApiError ? err.message : "Error de conexión.", true);
    }
  }

  function goToPage(page) {
    currentPage = page;
    loadHaciendas();
  }

  function changePageSize(e) {
    pageSize = parseInt(e.target.value);
    currentPage = 1;
    loadHaciendas();
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

<div class="haciendas-page">
  <div class="page-header">
    <h1>Haciendas</h1>
    <button class="btn btn-primary" onclick={openCreate}>+ Nueva Hacienda</button>
  </div>

  {#if resultMsg}
    <div class="result-banner" class:result-error={resultError}>{resultMsg}</div>
  {/if}

  {#if loading}
    <div class="loading">Cargando haciendas...</div>
  {:else if loadError}
    <div class="error-box">
      <p>{loadError}</p>
      <button class="btn btn-secondary" onclick={loadHaciendas}>Reintentar</button>
    </div>
  {:else if emptyMsg}
    <div class="empty-box">
      <span class="empty-icon">🏠</span>
      <p>{emptyMsg}</p>
    </div>
  {:else}
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Nombre</th>
            <th>Creado</th>
            <th>Actualizado</th>
            <th>Creado por</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each haciendas as h}
            <tr>
              <td>{h.codigo || "—"}</td>
              <td>{h.nombre || "—"}</td>
              <td>{formatDate(h.created_at)}</td>
              <td>{formatDate(h.updated_at)}</td>
              <td>{h.created_by_username || "—"}</td>
              <td class="actions-cell">
                <button class="btn-action" onclick={() => openEdit(h)} title="Editar">✏️</button>
                {#if allowDelete}
                  <button class="btn-action" onclick={() => openDelete(h)} title="Eliminar">🗑️</button>
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
            <option value={10}>10 por página</option>
            <option value={20}>20 por página</option>
            <option value={50}>50 por página</option>
            <option value={100}>100 por página</option>
          </select>
          Página {currentPage} de {totalPages} ({totalItems} registros)</span>
          <button class="btn-page" disabled={currentPage >= totalPages} onclick={() => goToPage(currentPage + 1)}>Siguiente</button>
        </div>
      {/if}
    </div>
  {/if}
</div>

<HaciendaFormModal
  show={formShow}
  mode={formMode}
  hacienda={formHacienda}
  error={formError}
  onClose={closeForm}
  onSave={handleFormSave}
/>

<ConfirmModal
  show={confirmShow}
  title="Eliminar Hacienda"
  message={confirmTarget ? `¿Está seguro de eliminar la hacienda ${confirmTarget.nombre}? (eliminación lógica)` : ""}
  confirmText="Eliminar"
  cancelText="Cancelar"
  onConfirm={confirmDelete}
  onCancel={cancelDelete}
/>

<style>
  .haciendas-page { max-width: 1000px; }
  .page-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 24px;
  }
  .page-header h1 { font-size: 24px; }
  .result-banner {
    padding: 12px 18px; border-radius: 8px; font-size: 14px; font-weight: 500;
    margin-bottom: 16px;
    background: rgba(81, 207, 102, 0.1); color: var(--success);
    border: 1px solid var(--success);
  }
  .result-error {
    background: rgba(255, 107, 107, 0.1); color: var(--error); border-color: var(--error);
  }
  .loading { color: var(--text-secondary); font-size: 15px; padding: 24px 0; }
  .error-box { text-align: center; padding: 40px 0; color: var(--error); }
  .empty-box { text-align: center; padding: 60px 0; color: var(--text-secondary); }
  .empty-icon { font-size: 48px; display: block; margin-bottom: 12px; opacity: 0.4; }
  .table-wrapper { overflow-x: auto; border: 1px solid var(--border); border-radius: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th {
    text-align: left; padding: 12px 16px; background: var(--bg-secondary);
    color: var(--text-secondary); font-weight: 600; font-size: 12px;
    text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border);
  }
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

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    margin-top: 16px;
    padding: 12px;
  }
  .page-info {
    font-size: 14px;
    color: var(--text-secondary);
  }
  .btn-page {
    padding: 8px 16px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
    font-size: 14px;
  }
  .btn-page:hover:not(:disabled) { background: var(--accent); color: white; }
  .btn-page:disabled { opacity: 0.4; cursor: not-allowed; }
  .page-size-select { padding: 6px 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-input); color: var(--text-primary); font-size: 13px; cursor: pointer; }

</style>