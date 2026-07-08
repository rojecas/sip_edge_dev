<script>
  /**
   * AdminAnomalias — Anomaly history table with pagination + "Detectar Ahora" panel.
   * Loads from GET /api/anomalies/history (paginated).
   */
  import { onMount } from "svelte";
  import { api, ApiError, buildQuery } from "../lib/api.js";
  import { ENDPOINTS, HARVEST_TYPES } from "../lib/constants.js";

  // ── History state ──────────────────────────────────────────────
  let anomalias = $state([]);
  let loading = $state(true);
  let loadError = $state("");
  let emptyMsg = $state("");
  let currentPage = $state(1);
  let totalPages = $state(1);
  let totalItems = $state(0);
  let pageSize = $state(20);

  // ── Detect on demand state ─────────────────────────────────────
  let detectPanelOpen = $state(false);
  let detectWindow = $state(120);
  let detectThreshold = $state(3.0);
  let detectTipoCosecha = $state("");
  let detectResults = $state([]);
  let detectLoading = $state(false);
  let detectError = $state("");
  let detectEmpty = $state(false);

  // ── Result message ─────────────────────────────────────────────
  let resultMsg = $state("");
  let resultError = $state(false);

  onMount(() => { loadHistory(); });

  // ── History ────────────────────────────────────────────────────
  async function loadHistory() {
    loading = true;
    loadError = "";
    emptyMsg = "";
    try {
      const qs = buildQuery({ page: currentPage, page_size: pageSize });
      const result = await api.get(`${ENDPOINTS.ANOMALIES_HISTORY}${qs}`);
      anomalias = result.items || [];
      currentPage = result.page || 1;
      totalPages = result.total_pages || 1;
      totalItems = result.total || 0;
      if (!anomalias || anomalias.length === 0) {
        emptyMsg = "No hay anomalías registradas";
        anomalias = [];
      }
    } catch (err) {
      loadError = err instanceof ApiError ? err.message : "Error de conexión. Verifique que el servidor esté disponible.";
    } finally {
      loading = false;
    }
  }

  function goToPage(page) {
    currentPage = page;
    loadHistory();
  }

  function changePageSize(e) {
    pageSize = parseInt(e.target.value);
    currentPage = 1;
    loadHistory();
  }

  // ── Detect on demand ───────────────────────────────────────────
  function toggleDetectPanel() {
    detectPanelOpen = !detectPanelOpen;
    detectResults = [];
    detectEmpty = false;
    detectError = "";
  }

  async function runDetection() {
    detectLoading = true;
    detectError = "";
    detectResults = [];
    detectEmpty = false;
    resultMsg = "";

    const params = {
      window: detectWindow,
      threshold: detectThreshold,
    };
    if (detectTipoCosecha) {
      params.tipo_cosecha = detectTipoCosecha;
    }

    try {
      const qs = buildQuery(params);
      const results = await api.get(`${ENDPOINTS.ANOMALIES_DETECT}${qs}`);
      if (!Array.isArray(results) || results.length === 0) {
        detectEmpty = true;
        detectResults = [];
      } else {
        detectResults = results;
      }
    } catch (err) {
      detectError = err instanceof ApiError ? err.message : "Error de conexión.";
    } finally {
      detectLoading = false;
    }
  }

  // ── Formatters ─────────────────────────────────────────────────
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

  function formatZScore(z) {
    if (z === null || z === undefined) return "—";
    return z.toFixed(2);
  }

  function formatNumber(n) {
    if (n === null || n === undefined) return "—";
    return typeof n === "number" ? n.toFixed(2) : String(n);
  }
</script>

<div class="anomalias-page">
  <div class="page-header">
    <h1>Anomalías</h1>
    <div class="header-actions">
      <button class="btn btn-secondary" onclick={toggleDetectPanel}>
        {detectPanelOpen ? "Cerrar Panel" : "Detectar Ahora"}
      </button>
      <button class="btn btn-secondary" onclick={loadHistory} disabled={loading}>
        {loading ? "Cargando..." : "Refrescar"}
      </button>
    </div>
  </div>

  {#if resultMsg}
    <div class="result-banner" class:result-error={resultError}>{resultMsg}</div>
  {/if}

  <!-- ── Detect on demand panel ── -->
  {#if detectPanelOpen}
    <div class="detect-panel">
      <h3>Detección bajo demanda</h3>
      <div class="detect-params">
        <label>
          Tamaño de ventana
          <input type="number" bind:value={detectWindow} min="1" max="1000" />
        </label>
        <label>
          Umbral Z-Score
          <input type="number" bind:value={detectThreshold} step="0.1" min="0.1" max="10.0" />
        </label>
        <label>
          Tipo de cosecha
          <select bind:value={detectTipoCosecha}>
            <option value="">Todas</option>
            {#each HARVEST_TYPES as ht}
              <option value={ht}>{ht}</option>
            {/each}
          </select>
        </label>
      </div>
      <button class="btn btn-primary" onclick={runDetection} disabled={detectLoading}>
        {detectLoading ? "Detectando..." : "Ejecutar Detección"}
      </button>

      {#if detectLoading}
        <div class="loading-inline">Ejecutando detección de anomalías...</div>
      {/if}

      {#if detectError}
        <div class="error-box">
          <p>{detectError}</p>
          <button class="btn btn-secondary" onclick={runDetection}>Reintentar</button>
        </div>
      {/if}

      {#if detectEmpty}
        <div class="empty-box">
          <span class="empty-icon">✅</span>
          <p>No se detectaron anomalías con los parámetros seleccionados.</p>
        </div>
      {/if}

      {#if detectResults.length > 0}
        <div class="table-wrapper" style="margin-top: 16px;">
          <table>
            <thead>
              <tr>
                <th>Record ID</th>
                <th>Capa</th>
                <th>Z-Score</th>
                <th>Valor Métrica</th>
                <th>Umbral</th>
                <th>Detalle</th>
              </tr>
            </thead>
            <tbody>
              {#each detectResults as r}
                <tr>
                  <td>{r.record_id}</td>
                  <td>{r.layer}</td>
                  <td>{formatZScore(r.z_score)}</td>
                  <td>{formatNumber(r.metric_value)}</td>
                  <td>{formatNumber(r.threshold)}</td>
                  <td class="col-detail">{r.detail || "—"}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    </div>
  {/if}

  <!-- ── History table ── -->
  {#if loading}
    <div class="loading">Cargando historial de anomalías...</div>
  {:else if loadError}
    <div class="error-box">
      <p>{loadError}</p>
      <button class="btn btn-secondary" onclick={loadHistory}>Reintentar</button>
    </div>
  {:else if emptyMsg}
    <div class="empty-box">
      <span class="empty-icon">⚠️</span>
      <p>{emptyMsg}</p>
    </div>
  {:else}
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Capa</th>
            <th>Z-Score</th>
            <th>Valor Métrica</th>
            <th>Umbral</th>
            <th>Reporte LLM</th>
            <th>SMS Enviado</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody>
          {#each anomalias as a}
            <tr>
              <td>{a.id}</td>
              <td>{a.layer}</td>
              <td>{formatZScore(a.z_score)}</td>
              <td>{formatNumber(a.metric_value)}</td>
              <td>{formatNumber(a.threshold)}</td>
              <td class="col-report">{a.llm_report || "—"}</td>
              <td>{a.sent_sms ? "Sí" : "No"}</td>
              <td>{formatDate(a.created_at)}</td>
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
            Página {currentPage} de {totalPages} ({totalItems} registros)
          </span>
          <button class="btn-page" disabled={currentPage >= totalPages} onclick={() => goToPage(currentPage + 1)}>Siguiente</button>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .anomalias-page { max-width: 1200px; }
  .page-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
  }
  .page-header h1 { font-size: 24px; }
  .header-actions { display: flex; gap: 10px; }
  .result-banner {
    padding: 12px 18px; border-radius: 8px; font-size: 14px; font-weight: 500;
    margin-bottom: 16px;
    background: rgba(81, 207, 102, 0.1); color: var(--success);
    border: 1px solid var(--success);
  }
  .result-error {
    background: rgba(255, 107, 107, 0.1); color: var(--error); border-color: var(--error);
  }
  .detect-panel {
    margin-bottom: 24px; padding: 20px;
    border: 1px solid var(--border); border-radius: 12px;
    background: var(--bg-secondary);
  }
  .detect-panel h3 { margin: 0 0 16px; font-size: 16px; }
  .detect-params {
    display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px;
  }
  .detect-params label {
    display: flex; flex-direction: column; gap: 4px;
    font-size: 13px; color: var(--text-secondary);
  }
  .detect-params input,
  .detect-params select {
    padding: 8px 12px; border: 1px solid var(--border);
    border-radius: 8px; background: var(--bg-input);
    color: var(--text-primary); font-size: 14px; width: 160px;
  }
  .detect-params input:focus,
  .detect-params select:focus {
    outline: none; border-color: var(--accent);
  }
  .loading { color: var(--text-secondary); font-size: 15px; padding: 24px 0; }
  .loading-inline { color: var(--text-secondary); font-size: 14px; padding: 12px 0; }
  .error-box { text-align: center; padding: 16px 0; color: var(--error); }
  .empty-box { text-align: center; padding: 40px 0; color: var(--text-secondary); }
  .empty-icon { font-size: 48px; display: block; margin-bottom: 12px; opacity: 0.4; }
  .table-wrapper { overflow-x: auto; border: 1px solid var(--border); border-radius: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 12px 16px; background: var(--bg-secondary); color: var(--text-secondary); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
  td { padding: 10px 16px; border-bottom: 1px solid var(--border); color: var(--text-primary); white-space: nowrap; }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr:hover { background: rgba(255, 255, 255, 0.02); }
  .col-report { max-width: 250px; overflow: hidden; text-overflow: ellipsis; }
  .col-detail { max-width: 300px; overflow: hidden; text-overflow: ellipsis; }
  .btn { padding: 10px 20px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; white-space: nowrap; }
  .btn:disabled { opacity: 0.6; cursor: not-allowed; }
  .btn-primary { background: var(--accent); color: white; }
  .btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
  .btn-secondary { background: var(--bg-input); color: var(--text-primary); border: 1px solid var(--border); }
  .btn-secondary:hover:not(:disabled) { background: var(--border); }
  .pagination {
    display: flex; justify-content: center; align-items: center;
    gap: 16px; margin-top: 16px; padding: 12px;
  }
  .page-info { font-size: 14px; color: var(--text-secondary); }
  .btn-page {
    padding: 8px 16px; border: 1px solid var(--border);
    border-radius: 6px; background: var(--bg-secondary);
    color: var(--text-primary); cursor: pointer; font-size: 14px;
  }
  .btn-page:hover:not(:disabled) { background: var(--accent); color: white; }
  .btn-page:disabled { opacity: 0.4; cursor: not-allowed; }
  .page-size-select { padding: 6px 8px; border: 1px solid var(--border); border-radius: 6px; background: var(--bg-input); color: var(--text-primary); font-size: 13px; cursor: pointer; }
</style>
