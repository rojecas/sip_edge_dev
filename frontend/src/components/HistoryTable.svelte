<script>
  /**
   * HistoryTable — Operator's weighing history with pagination and date filter.
   * Columns: ID, Fecha, Hora, Tractomula, Vagon, Guia, Hacienda, Suerte,
   *          Peso Muestra, Peso Mineral, Peso Vegetal.
   */
  import { onMount } from "svelte";
  import { api, ApiError, buildQuery } from "../lib/api.js";
  import { ENDPOINTS, CONFIG } from "../lib/constants.js";
  import { authStore } from "../stores/auth.js";
  import WeighingDetailModal from "./WeighingDetailModal.svelte";

  // Data
  let items = $state([]);
  let total = $state(0);
  let page = $state(1);
  let pageSize = $state("10");
  let totalPages = $state(1);

  // Filters
  let startDate = $state("");
  let endDate = $state("");

  // State
  let isLoading = $state(false);
  let errorMessage = $state("");
  let emptyFilterMessage = $state("");
  let selectedWeighing = $state(null);
  let showDetail = $state(false);

  onMount(() => {
    loadData();
  });

  async function loadData(resetPage = false) {
    if (resetPage) {
      page = 1;
    }
    isLoading = true;
    errorMessage = "";
    emptyFilterMessage = "";

    try {
      const params = {
        page: page,
        page_size: pageSize,
        sort_by: "fecha",
        sort_order: "desc",
      };
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const data = await api.get(`${ENDPOINTS.WEIGHINGS}${buildQuery(params)}`);
      items = data.items || [];
      total = data.total || 0;
      page = data.page || page;
      // pageSize kept from user interaction
      totalPages = data.total_pages || 1;

      if (total === 0 && (startDate || endDate)) {
        emptyFilterMessage = "No se encontraron registros para el filtro seleccionado";
      }
    } catch (err) {
      if (err instanceof ApiError) {
        errorMessage = err.message;
      } else {
        errorMessage = "Error al cargar el historial";
      }
    } finally {
      isLoading = false;
    }
  }

  function prevPage() {
    if (page > 1) {
      page = page - 1;
      loadData();
    }
  }

  function nextPage() {
    if (page < totalPages) {
      page = page + 1;
      loadData();
    }
  }

  function onPageSizeChange(e) {
    pageSize = e.target.value;
    page = 1;
    loadData();
  }

  function applyFilter() {
    loadData(true);
  }

  function clearFilter() {
    startDate = "";
    endDate = "";
    emptyFilterMessage = "";
    loadData(true);
  }

  function formatDecimal(val) {
    if (val === null || val === undefined) return "—";
    return Number(val).toFixed(3);
  }

  async function handleResend(weighingId) {
    try {
      await api.post(`${ENDPOINTS.WEIGHINGS_RESEND}/${weighingId}/resend`);
      // Reload table to reflect the change in enviado_pc
      await loadData();
    } catch {
      // Error silently handled — user knows from button state
    }
  }
</script>

<div class="history-container">
  <h2>Historial de Pesajes</h2>

  <!-- Date filter -->
  <div class="filter-bar">
    <div class="filter-fields">
      <div class="filter-field">
        <label for="start-date">Desde</label>
        <input
          id="start-date"
          type="date"
          bind:value={startDate}
          class="date-input"
        />
      </div>
      <div class="filter-field">
        <label for="end-date">Hasta</label>
        <input
          id="end-date"
          type="date"
          bind:value={endDate}
          class="date-input"
        />
      </div>
    </div>
    <div class="filter-actions">
      <button class="btn-filter" onclick={applyFilter}>Filtrar</button>
      {#if startDate || endDate}
        <button class="btn-clear" onclick={clearFilter}>Limpiar</button>
      {/if}
    </div>
  </div>

  <!-- Loading -->
  {#if isLoading}
    <div class="loading">Cargando historial...</div>
  {:else if errorMessage}
    <div class="error-box">
      <p>{errorMessage}</p>
      <button class="btn-retry" onclick={() => loadData()}>Reintentar</button>
    </div>
  {:else if emptyFilterMessage}
    <div class="empty">{emptyFilterMessage}</div>
  {:else if items.length === 0}
    <div class="empty">No hay pesajes registrados</div>
  {:else}
    <!-- Table -->
    <div class="table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Hora</th>
            <th>Tractomula</th>
            <th>Vagón</th>
            <th>Guía</th>
            <th>Hacienda</th>
            <th>Suerte</th>
            <th>Tipo Cosecha</th>
            <th>Peso Muestra</th>
            <th>Peso Mineral</th>
            <th>Peso Vegetal</th>
            <th>Acción</th>
          </tr>
        </thead>
        <tbody>
          {#each items as w}
            <tr onclick={() => { selectedWeighing = w; showDetail = true; }}>
              <td>{w.fecha}</td>
              <td>{w.hora}</td>
              <td>{w.tractomula || "—"}</td>
              <td>{w.vagon || "—"}</td>
              <td>{w.numero_guia || "—"}</td>
              <td>{w.hacienda_id}</td>
              <td>{w.suerte_id}</td>
              <td>{w.tipo_cosecha || "—"}</td>
              <td class="num">{formatDecimal(w.peso_muestra)}</td>
              <td class="num">{formatDecimal(w.peso_mineral)}</td>
              <td class="num">{formatDecimal(w.peso_vegetal_extrano)}</td>
              <td>
                {#if $authStore.isAdmin}
                  <button class="btn-action" onclick={(e) => { e.stopPropagation(); handleResend(w.id); }}
                    title="Reenviar datos al PC">&#x1F504;</button>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div class="pagination">
      <div class="pagination-info">
        <span>Página {page} de {totalPages}</span>
        <span class="total-info">({total} registros)</span>
      </div>

      <div class="pagination-controls">
        <button
          class="btn-page"
          onclick={prevPage}
          disabled={page <= 1}
        >Anterior</button>

        <select bind:value={pageSize} onchange={onPageSizeChange} class="page-size-select">
          <option value="10">10 por página</option>
          <option value="20">20 por página</option>
          <option value="50">50 por página</option>
        </select>

        <button
          class="btn-page"
          onclick={nextPage}
          disabled={page >= totalPages}
        >Siguiente</button>
      </div>
    </div>
  {/if}

  {#if showDetail && selectedWeighing}
    <WeighingDetailModal
      weighing={selectedWeighing}
      onclose={() => showDetail = false}
    />
  {/if}
</div>

<style>
  .history-container {
    max-width: 1200px;
    margin: 0 auto;
  }

  h2 {
    font-size: 22px;
    margin-bottom: 20px;
    color: var(--text-primary);
  }

  .filter-bar {
    display: flex;
    align-items: flex-end;
    gap: 16px;
    margin-bottom: 20px;
    padding: 16px;
    background: var(--bg-secondary);
    border-radius: 8px;
    flex-wrap: wrap;
  }

  .filter-fields {
    display: flex;
    gap: 12px;
  }

  .filter-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .filter-field label {
    font-size: 13px;
    color: var(--text-secondary);
    font-weight: 600;
  }

  .date-input {
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 14px;
    outline: none;
  }

  .date-input:focus {
    border-color: var(--accent);
  }

  .filter-actions {
    display: flex;
    gap: 8px;
  }

  .btn-filter {
    padding: 8px 20px;
    border: none;
    border-radius: 6px;
    background: var(--accent);
    color: white;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
  }

  .btn-filter:hover {
    background: var(--accent-hover);
  }

  .btn-clear {
    padding: 8px 20px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 14px;
    cursor: pointer;
  }

  .btn-clear:hover {
    background: var(--bg-input);
  }

  .loading {
    padding: 40px;
    text-align: center;
    color: var(--text-secondary);
    font-size: 16px;
  }

  .error-box {
    text-align: center;
    padding: 40px;
  }

  .error-box p {
    color: var(--error);
    margin: 0 0 16px;
  }

  .btn-retry {
    padding: 10px 24px;
    border: none;
    border-radius: 6px;
    background: var(--accent);
    color: white;
    cursor: pointer;
  }

  .empty {
    padding: 40px;
    text-align: center;
    color: var(--text-secondary);
    font-size: 16px;
  }

  .table-wrapper {
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-secondary);
  }

  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }

  .data-table th {
    padding: 12px 10px;
    background: var(--bg-input);
    color: var(--text-secondary);
    font-weight: 600;
    text-align: left;
    white-space: nowrap;
    border-bottom: 2px solid var(--border);
  }

  .data-table td {
    padding: 10px;
    border-bottom: 1px solid var(--border);
    color: var(--text-primary);
    white-space: nowrap;
  }

  .data-table tr:last-child td {
    border-bottom: none;
  }

  .data-table tbody tr {
    cursor: pointer;
  }

  .data-table tr:hover td {
    background: rgba(233, 69, 96, 0.05);
  }

  .data-table .num {
    text-align: right;
    font-family: "Courier New", monospace;
  }

  .pagination {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
    padding: 12px 0;
    flex-wrap: wrap;
    gap: 12px;
  }

  .pagination-info {
    display: flex;
    gap: 12px;
    align-items: baseline;
    font-size: 14px;
    color: var(--text-secondary);
  }

  .total-info {
    font-size: 13px;
    opacity: 0.7;
  }

  .pagination-controls {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .btn-page {
    padding: 8px 16px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-page:hover:not(:disabled) {
    background: var(--bg-input);
  }

  .btn-page:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .page-size-select {
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 13px;
    cursor: pointer;
  }

  .btn-action {
    padding: 4px 8px;
    border: none;
    border-radius: 4px;
    background: var(--accent);
    color: white;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-action:hover {
    background: var(--accent-hover);
  }
</style>
