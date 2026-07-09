<script>
  /**
   * AdminReportes — CRUD view for report templates.
   * Loads from GET /api/reports/templates, supports create/edit/delete.
   */
  import { onMount } from "svelte";
  import { api, ApiError } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";
  import TemplateFormModal from "./TemplateFormModal.svelte";
  import ConfirmModal from "./ConfirmModal.svelte";

  let plantillas = $state([]);
  let loading = $state(true);
  let loadError = $state("");
  let emptyMsg = $state("");

  // Modal state
  let formShow = $state(false);
  let formMode = $state("create");
  let formPlantilla = $state(null);
  let formError = $state("");

  // Delete confirm modal state
  let delModalShow = $state(false);
  let delPlantilla = $state(null);

  // Success message
  let successMsg = $state("");
  let successTimer = null;

  onMount(() => { loadPlantillas(); });

  async function loadPlantillas() {
    loading = true;
    loadError = "";
    emptyMsg = "";
    try {
      const result = await api.get(ENDPOINTS.REPORTS_TEMPLATES);
      plantillas = Array.isArray(result) ? result : (result.items || []);
      if (!plantillas || plantillas.length === 0) {
        emptyMsg = "No hay plantillas de reportes";
        plantillas = [];
      }
    } catch (err) {
      loadError = err instanceof ApiError ? err.message : "Error de conexión. Verifique que el servidor esté disponible.";
    } finally {
      loading = false;
    }
  }

  function showSuccess(msg) {
    successMsg = msg;
    if (successTimer) clearTimeout(successTimer);
    successTimer = setTimeout(() => { successMsg = ""; }, 4000);
  }

  function openCreate() {
    formMode = "create";
    formPlantilla = null;
    formError = "";
    formShow = true;
  }

  function openEdit(plantilla) {
    formMode = "edit";
    formPlantilla = plantilla;
    formError = "";
    formShow = true;
  }

  function closeForm() {
    formShow = false;
    formPlantilla = null;
    formError = "";
  }

  async function handleSave(payload) {
    formError = "";
    try {
      if (formMode === "create") {
        await api.post(ENDPOINTS.REPORTS_TEMPLATES, payload);
        showSuccess("Plantilla creada exitosamente.");
      } else {
        await api.put(ENDPOINTS.REPORTS_TEMPLATES_BY_ID + formPlantilla.id, payload);
        showSuccess("Plantilla actualizada exitosamente.");
      }
      closeForm();
      await loadPlantillas();
    } catch (err) {
      formError = err instanceof ApiError ? err.message : "Error de conexión.";
    }
  }

  function confirmDelete(plantilla) {
    delPlantilla = plantilla;
    delModalShow = true;
  }

  async function handleDelete() {
    if (!delPlantilla) return;
    try {
      await api.del(ENDPOINTS.REPORTS_TEMPLATES_BY_ID + delPlantilla.id);
      showSuccess("Plantilla eliminada exitosamente.");
      delModalShow = false;
      delPlantilla = null;
      await loadPlantillas();
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Error de conexión.";
      showSuccess(msg);
      delModalShow = false;
      delPlantilla = null;
    }
  }

  function formatSchedule(schedule) {
    if (!Array.isArray(schedule) || schedule.length === 0) return "—";
    return schedule.join(", ");
  }

  function formatMetrics(metrics) {
    if (!Array.isArray(metrics) || metrics.length === 0) return "—";
    return metrics.join(", ");
  }
</script>

<div class="reportes-page">
  <div class="page-header">
    <h1>Reportes Programados</h1>
    <div class="header-actions">
      <button class="btn btn-secondary" onclick={loadPlantillas} disabled={loading}>
        {loading ? "Cargando..." : "Refrescar"}
      </button>
      <button class="btn btn-primary" onclick={openCreate}>
        + Nueva Plantilla
      </button>
    </div>
  </div>

  {#if successMsg}
    <div class="success-banner">{successMsg}</div>
  {/if}

  {#if loading}
    <div class="loading">Cargando plantillas de reportes...</div>
  {:else if loadError}
    <div class="error-box">
      <p>{loadError}</p>
      <button class="btn btn-secondary" onclick={loadPlantillas}>Reintentar</button>
    </div>
  {:else if emptyMsg}
    <div class="empty-box">
      <span class="empty-icon">📋</span>
      <p>{emptyMsg}</p>
    </div>
  {:else}
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Schedule</th>
            <th>Métricas</th>
            <th>Activo</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {#each plantillas as p}
            <tr>
              <td class="col-name">{p.name || "—"}</td>
              <td class="col-schedule">{formatSchedule(p.schedule)}</td>
              <td class="col-metrics">{formatMetrics(p.metrics)}</td>
              <td>{p.is_active ? "Sí" : "No"}</td>
              <td class="col-actions">
                <button class="btn-action" onclick={() => openEdit(p)} title="Editar">✏️</button>
                <button class="btn-action" onclick={() => confirmDelete(p)} title="Eliminar">🗑️</button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<!-- Create/Edit Modal -->
<TemplateFormModal
  show={formShow}
  mode={formMode}
  plantilla={formPlantilla}
  error={formError}
  onClose={closeForm}
  onSave={handleSave}
/>

<!-- Delete Confirm Modal -->
<ConfirmModal
  show={delModalShow}
  title="Eliminar Plantilla"
  message={delPlantilla ? `¿Eliminar la plantilla "${delPlantilla.name}"?` : ""}
  confirmText="Eliminar"
  cancelText="Cancelar"
  onConfirm={handleDelete}
  onCancel={() => { delModalShow = false; delPlantilla = null; }}
/>

<style>
  .reportes-page { max-width: 1200px; }
  .page-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
  }
  .page-header h1 { font-size: 24px; }
  .header-actions { display: flex; gap: 10px; }
  .success-banner {
    padding: 12px 18px; border-radius: 8px; font-size: 14px; font-weight: 500;
    margin-bottom: 16px;
    background: rgba(81, 207, 102, 0.1); color: var(--success);
    border: 1px solid var(--success);
  }
  .loading { color: var(--text-secondary); font-size: 15px; padding: 24px 0; }
  .error-box { text-align: center; padding: 40px 0; color: var(--error); }
  .empty-box { text-align: center; padding: 60px 0; color: var(--text-secondary); }
  .empty-icon { font-size: 48px; display: block; margin-bottom: 12px; opacity: 0.4; }
  .table-wrapper { overflow-x: auto; border: 1px solid var(--border); border-radius: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 12px 16px; background: var(--bg-secondary); color: var(--text-secondary); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
  td { padding: 10px 16px; border-bottom: 1px solid var(--border); color: var(--text-primary); }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr:hover { background: rgba(255, 255, 255, 0.02); }
  .col-name { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .col-schedule { max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .col-metrics { max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .col-actions { white-space: nowrap; }
  .btn { padding: 10px 20px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; white-space: nowrap; }
  .btn:disabled { opacity: 0.6; cursor: not-allowed; }
  .btn-primary { background: var(--accent); color: white; }
  .btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
  .btn-secondary { background: var(--bg-input); color: var(--text-primary); border: 1px solid var(--border); }
  .btn-secondary:hover:not(:disabled) { background: var(--border); }
  .btn-action {
    background: none; border: none; cursor: pointer; font-size: 16px;
    padding: 4px 6px; border-radius: 4px; transition: background 0.2s;
  }
  .btn-action:hover { background: var(--bg-input); }
</style>
