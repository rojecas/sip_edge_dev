<script>
  /**
   * WeighingDetailModal — Modal showing full weighing detail.
   * Props: weighing (object), onclose (callback).
   * Closes on: X button, Escape key, or click outside panel.
   */
  import { onMount, onDestroy } from "svelte";

  let { weighing, onclose } = $props();

  function handleKeydown(e) {
    if (e.key === "Escape") {
      onclose();
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeydown);
    return () => {
      window.removeEventListener("keydown", handleKeydown);
    };
  });

  function handleOverlayClick(e) {
    if (e.target === e.currentTarget) {
      onclose();
    }
  }

  function formatDecimal(val) {
    if (val === null || val === undefined) return "—";
    return Number(val).toFixed(3);
  }

  function notasDisplay() {
    const n = (weighing.notas || "").trim();
    return n ? n : "Sin observaciones";
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="modal-overlay" onclick={handleOverlayClick} role="dialog" aria-modal="true">
  <div class="modal-panel">
    <div class="modal-header">
      <h2>Detalle del Pesaje #{weighing.id}</h2>
      <button class="modal-close" onclick={onclose} aria-label="Cerrar">&times;</button>
    </div>

    <div class="modal-body">
      <div class="detail-grid">
        <div class="detail-row">
          <span class="detail-label">Fecha</span>
          <span class="detail-value">{weighing.fecha || "—"}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Hora</span>
          <span class="detail-value">{weighing.hora || "—"}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Tractomula</span>
          <span class="detail-value">{weighing.tractomula || "—"}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Vagón</span>
          <span class="detail-value">{weighing.vagon || "—"}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Guía</span>
          <span class="detail-value">{weighing.numero_guia || "—"}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Hacienda</span>
          <span class="detail-value">{weighing.hacienda_id || "—"}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Suerte</span>
          <span class="detail-value">{weighing.suerte_id || "—"}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Tipo Cosecha</span>
          <span class="detail-value">{weighing.tipo_cosecha || "—"}</span>
        </div>
      </div>

      <div class="pesos-section">
        <h3>Pesos (kg)</h3>
        <div class="pesos-grid">
          <div class="peso-item">
            <span class="peso-label">Muestra</span>
            <span class="peso-value">{formatDecimal(weighing.peso_muestra)}</span>
          </div>
          <div class="peso-item">
            <span class="peso-label">Mineral</span>
            <span class="peso-value">{formatDecimal(weighing.peso_mineral)}</span>
          </div>
          <div class="peso-item">
            <span class="peso-label">Vegetal</span>
            <span class="peso-value">{formatDecimal(weighing.peso_vegetal_extrano)}</span>
          </div>
        </div>
      </div>

      <div class="notas-section">
        <h3>Notas</h3>
        <p class="notas-content">{notasDisplay()}</p>
      </div>
    </div>
  </div>
</div>

<style>
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s ease;
  }

  .modal-panel {
    background: var(--bg-secondary);
    border-radius: 12px;
    width: 90%;
    max-width: 580px;
    max-height: 85vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    animation: slideUp 0.25s ease;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
  }

  .modal-header h2 {
    font-size: 18px;
    margin: 0;
    color: var(--text-primary);
  }

  .modal-close {
    background: none;
    border: none;
    font-size: 28px;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
  }

  .modal-close:hover {
    color: var(--text-primary);
  }

  .modal-body {
    padding: 20px;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 20px;
  }

  .detail-row {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .detail-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .detail-value {
    font-size: 15px;
    color: var(--text-primary);
  }

  .pesos-section {
    margin-bottom: 20px;
    padding: 14px;
    background: var(--bg-input);
    border-radius: 8px;
    border: 1px solid var(--border);
  }

  .pesos-section h3,
  .notas-section h3 {
    font-size: 14px;
    color: var(--text-secondary);
    margin: 0 0 10px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
  }

  .pesos-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 12px;
  }

  .peso-item {
    text-align: center;
  }

  .peso-label {
    display: block;
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 4px;
  }

  .peso-value {
    display: block;
    font-size: 18px;
    font-weight: 700;
    color: var(--accent);
    font-family: "Courier New", monospace;
  }

  .notas-section {
    background: var(--bg-input);
    border-radius: 8px;
    padding: 14px;
    border: 1px solid var(--border);
  }

  .notas-content {
    font-size: 14px;
    color: var(--text-primary);
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
