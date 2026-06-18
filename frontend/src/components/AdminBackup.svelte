<script>
  /**
   * AdminBackup — Backup panel: history table, run backup, refresh.
   */
  import { onMount } from "svelte";
  import { api, ApiError } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";

  let backups = $state([]);
  let loading = $state(true);
  let loadError = $state("");
  let emptyMsg = $state("");

  let resultMsg = $state("");
  let resultError = $state(false);

  let running = $state(false);
  let runDisabled = $state(false);
  let runCountdown = $state(0);

  onMount(() => { loadBackups(); });

  async function loadBackups() {
    loading = true;
    loadError = "";
    emptyMsg = "";
    try {
      const result = await api.get(ENDPOINTS.BACKUP_STATUS);
      backups = result.items || result || [];
      if (!backups || backups.length === 0) {
        emptyMsg = "No hay registros de backup.";
        backups = [];
      }
    } catch (err) {
      loadError = err instanceof ApiError ? err.message : "Error de conexión. Verifique que el servidor esté disponible.";
    } finally {
      loading = false;
    }
  }

  async function runBackup() {
    running = true;
    resultMsg = "";
    try {
      await api.post(ENDPOINTS.BACKUP_RUN);
      // HTTP 202 success
      resultMsg = "Backup iniciado en segundo plano.";
      resultError = false;
      runDisabled = true;
      runCountdown = 30;
      // Countdown timer
      const timer = setInterval(() => {
        runCountdown--;
        if (runCountdown <= 0) {
          runDisabled = false;
          clearInterval(timer);
        }
      }, 1000);
    } catch (err) {
      resultMsg = err instanceof ApiError ? err.message : "Error de conexión.";
      resultError = true;
      // Do NOT disable button on error per R32
    } finally {
      running = false;
    }
  }

  function formatBytes(bytes) {
    if (bytes === null || bytes === undefined) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function formatDate(dateStr) {
    if (!dateStr) return "—";
    try {
      return new Date(dateStr).toLocaleString("es-CO", {
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", second: "2-digit",
      });
    } catch {
      return dateStr;
    }
  }
</script>

<div class="backup-page">
  <div class="page-header">
    <h1>Backup</h1>
    <div class="header-actions">
      <button class="btn btn-secondary" onclick={loadBackups} disabled={loading}>
        {loading ? "Cargando..." : "Refrescar"}
      </button>
      <button
        class="btn btn-primary"
        onclick={runBackup}
        disabled={running || runDisabled}
      >
        {#if running}
          Ejecutando...
        {:else if runDisabled}
          Procesando... ({runCountdown}s)
        {:else}
          Ejecutar Backup
        {/if}
      </button>
    </div>
  </div>

  {#if resultMsg}
    <div class="result-banner" class:result-error={resultError}>
      {resultMsg}
      {#if resultError}
        <button class="btn-link" onclick={runBackup}>Reintentar</button>
      {/if}
    </div>
  {/if}

  {#if loading}
    <div class="loading">Cargando historial de backups...</div>
  {:else if loadError}
    <div class="error-box">
      <p>{loadError}</p>
      <button class="btn btn-secondary" onclick={loadBackups}>Reintentar</button>
    </div>
  {:else if emptyMsg}
    <div class="empty-box">
      <span class="empty-icon">💾</span>
      <p>{emptyMsg}</p>
    </div>
  {:else}
    <div class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Archivo</th>
            <th>Tamaño</th>
            <th>Checksum Local</th>
            <th>Copia USB</th>
            <th>Checksum USB</th>
            <th>Error</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody>
          {#each backups as b}
            <tr>
              <td>{b.id}</td>
              <td class="col-file" title={b.archivo || ""}>{b.archivo || "—"}</td>
              <td>{formatBytes(b.tamano)}</td>
              <td class="col-checksum" title={b.checksum_local || ""}>{b.checksum_local || "—"}</td>
              <td>{b.copia_usb ? "Sí" : "No"}</td>
              <td class="col-checksum" title={b.checksum_usb || ""}>{b.checksum_usb || "—"}</td>
              <td class="col-error">{b.error || "—"}</td>
              <td>{formatDate(b.fecha)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

<style>
  .backup-page { max-width: 1200px; }
  .page-header {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
  }
  .page-header h1 { font-size: 24px; }
  .header-actions { display: flex; gap: 10px; }
  .result-banner {
    padding: 12px 18px; border-radius: 8px; font-size: 14px; font-weight: 500;
    margin-bottom: 16px; display: flex; align-items: center; gap: 12px;
    background: rgba(81, 207, 102, 0.1); color: var(--success);
    border: 1px solid var(--success);
  }
  .result-error {
    background: rgba(255, 107, 107, 0.1); color: var(--error); border-color: var(--error);
  }
  .btn-link {
    background: none; border: none; color: var(--accent); cursor: pointer;
    font-size: 13px; text-decoration: underline; padding: 0;
  }
  .loading { color: var(--text-secondary); font-size: 15px; padding: 24px 0; }
  .error-box { text-align: center; padding: 40px 0; color: var(--error); }
  .empty-box { text-align: center; padding: 60px 0; color: var(--text-secondary); }
  .empty-icon { font-size: 48px; display: block; margin-bottom: 12px; opacity: 0.4; }
  .table-wrapper { overflow-x: auto; border: 1px solid var(--border); border-radius: 12px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 12px 16px; background: var(--bg-secondary); color: var(--text-secondary); font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid var(--border); }
  td { padding: 10px 16px; border-bottom: 1px solid var(--border); color: var(--text-primary); white-space: nowrap; }
  tbody tr:last-child td { border-bottom: none; }
  tbody tr:hover { background: rgba(255, 255, 255, 0.02); }
  .col-file { max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
  .col-checksum { max-width: 120px; overflow: hidden; text-overflow: ellipsis; font-family: monospace; font-size: 11px; }
  .col-error { max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
  .btn { padding: 10px 20px; border: none; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: background 0.2s; white-space: nowrap; }
  .btn:disabled { opacity: 0.6; cursor: not-allowed; }
  .btn-primary { background: var(--accent); color: white; }
  .btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
  .btn-secondary { background: var(--bg-input); color: var(--text-primary); border: 1px solid var(--border); }
  .btn-secondary:hover:not(:disabled) { background: var(--border); }
</style>
