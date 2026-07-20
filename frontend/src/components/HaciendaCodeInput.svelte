<script>
  /**
   * HaciendaCodeInput — Shared component for entering hacienda code.
   * Encapsulates: text input, API search on Enter/Tab, confirmed display,
   * error modal, and clear button.
   *
   * Props:
   *   onSelect(hacienda: HaciendaResponse | null) — called when a hacienda is confirmed or cleared
   *   placeholder — optional placeholder text for the input
   *   resetKey — incremented by parent to trigger internal state reset
   */
  import { api, buildQuery } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";
  import { navigate } from "../lib/router.js";

  let { onSelect, placeholder = "Ingrese código de hacienda", resetKey = 0 } = $props();

  // Internal state
  let inputValue = $state("");
  let selectedHacienda = $state(null);   // HaciendaResponse when confirmed
  let showErrorModal = $state(false);
  let searchCode = $state("");           // code that failed to resolve
  let loading = $state(false);
  let inputRef = $state(null);

  // Reset internal state when parent increments resetKey (e.g. after form submit)
  $effect(() => {
    void resetKey;
    selectedHacienda = null;
    inputValue = "";
    searchCode = "";
    showErrorModal = false;
  });

  /**
   * Triggers API search for the hacienda code.
   * Fires only on Enter/Tab — NOT on each keystroke (R3).
   */
  async function searchHacienda() {
    const code = inputValue.trim();
    if (!code) return;

    loading = true;
    searchCode = code;
    try {
      const qs = buildQuery({ search: code, page_size: 1 });
      const data = await api.get(`${ENDPOINTS.HACIENDAS}${qs}`);
      if (data.items && data.items.length > 0) {
        const hacienda = data.items[0];
        selectedHacienda = hacienda;
        onSelect(hacienda);
        showErrorModal = false;
      } else {
        // No match found — show error modal (R7)
        selectedHacienda = null;
        showErrorModal = true;
      }
    } catch {
      showErrorModal = true;
    } finally {
      loading = false;
    }
  }

  function handleKeydown(e) {
    if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      searchHacienda();
    }
  }

  /**
   * Clear selection and reset input (R10).
   */
  function handleClear() {
    selectedHacienda = null;
    inputValue = "";
    searchCode = "";
    showErrorModal = false;
    onSelect(null);
    if (inputRef) {
      inputRef.focus();
    }
  }

  function handleRetry() {
    showErrorModal = false;
    if (inputRef) {
      inputRef.focus();
    }
  }

  function handleCreateNew() {
    showErrorModal = false;
    navigate("/kiosco/haciendas");
  }

  function handleOverlayClick(e) {
    if (e.target === e.currentTarget) {
      handleRetry();
    }
  }
</script>

<div class="hacienda-code-input">
  {#if selectedHacienda}
    <!-- Confirmed display: CODIGO - NOMBRE with clear button (R5, R6) -->
    <div class="confirmed-display">
      <span class="confirmed-text" title="{selectedHacienda.codigo} - {selectedHacienda.nombre}">
        {selectedHacienda.codigo} - {selectedHacienda.nombre}
      </span>
      <button
        type="button"
        class="btn-clear"
        onclick={handleClear}
        aria-label="Limpiar selección de hacienda"
        title="Limpiar"
      >&times;</button>
    </div>
  {:else}
    <!-- Text input for code entry -->
    <input
      type="text"
      bind:value={inputValue}
      bind:this={inputRef}
      onkeydown={handleKeydown}
      placeholder={placeholder}
      class="code-input"
      disabled={loading}
      aria-label="Código de hacienda"
    />
    {#if loading}
      <span class="loading-indicator">Buscando...</span>
    {/if}
  {/if}
</div>

<!-- Error Modal (R7, R8, R9) -->
{#if showErrorModal}
    <div class="modal-overlay" onclick={handleOverlayClick} onkeydown={(e) => e.key === "Escape" && handleRetry()} role="dialog" aria-modal="true" tabindex="-1">
    <div class="modal-container">
      <div class="modal-header">
        <h3>Código no encontrado</h3>
      </div>
      <div class="modal-body">
        <p class="modal-message">
          El código <strong>'{searchCode}'</strong> no corresponde a ninguna hacienda registrada.
        </p>
        <p class="modal-explanation">
          Esto puede deberse a un error de digitación o a una hacienda nueva que aún no ha sido creada.
        </p>
      </div>
      <div class="modal-actions">
        <button class="btn-retry" onclick={handleRetry}>
          Reintentar
        </button>
        <button class="btn-create" onclick={handleCreateNew}>
          Crear nueva hacienda
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .hacienda-code-input {
    position: relative;
  }

  .code-input {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 16px;
    outline: none;
    transition: border-color 0.2s;
  }

  .code-input:focus {
    border-color: var(--accent);
  }

  .code-input:disabled {
    opacity: 0.6;
  }

  .loading-indicator {
    position: absolute;
    right: 14px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 12px;
    color: var(--text-secondary);
  }

  .confirmed-display {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border: 1px solid var(--accent);
    border-radius: 8px;
    background: var(--bg-input);
  }

  .confirmed-text {
    flex: 1;
    font-size: 16px;
    color: var(--text-primary);
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .btn-clear {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 20px;
    font-weight: 700;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
    transition: color 0.2s;
    flex-shrink: 0;
  }

  .btn-clear:hover {
    color: var(--error);
  }

  /* Error Modal */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
  }

  .modal-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 28px;
    width: 100%;
    max-width: 480px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    margin-bottom: 16px;
  }

  .modal-header h3 {
    margin: 0;
    font-size: 18px;
    color: var(--error);
  }

  .modal-body {
    margin-bottom: 24px;
  }

  .modal-message {
    font-size: 15px;
    color: var(--text-primary);
    margin: 0 0 8px 0;
  }

  .modal-explanation {
    font-size: 13px;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.5;
  }

  .modal-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .btn-retry {
    padding: 10px 20px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-retry:hover {
    background: var(--bg-input);
  }

  .btn-create {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    background: var(--accent);
    color: white;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-create:hover {
    background: var(--accent-hover);
  }
</style>