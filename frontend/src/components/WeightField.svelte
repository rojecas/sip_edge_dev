<script>
  /**
   * WeightField — Reusable weight input field with Tara/Leer buttons.
   * Props: fieldName, bind:value, disabled (true when emergency mode active = editable).
   * When disabled=true (normal mode), field is readonly — only updated via Tara/Leer.
   * When disabled=false (emergency mode), field is editable manually.
   *
   * CORREGIDO (T38): Boton "Leer" llama a POST /api/scale/command (REXT).
   * Boton "Tara" llama a POST /api/scale/command (TARE).
   * Botones se deshabilitan durante la peticion (isLoading).
   */
  import { api } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";

  let {
    fieldName = "",
    value = $bindable(0),
    disabled = true,
    onTara = () => {},
    onLeer = () => {},
    onReset = null,
  } = $props();

  let isLoading = $state(false);

  async function handleTara() {
    if (isLoading) return;
    isLoading = true;
    try {
      const result = await api.post(ENDPOINTS.SCALE_COMMAND, { command: "TARE" });
      if (result && result.result === "ok") {
        value = 0;
        onTara?.();
      }
    } catch (err) {
      console.error(`Tara failed on ${fieldName}:`, err.message || err);
    } finally {
      isLoading = false;
    }
  }

  async function handleLeer() {
    if (isLoading) return;
    isLoading = true;
    try {
      const result = await api.post(ENDPOINTS.SCALE_COMMAND, { command: "REXT" });
      if (result && result.net_weight !== undefined) {
        value = result.net_weight;
        onLeer?.();
      }
    } catch (err) {
      console.error(`REXT failed on ${fieldName}:`, err.message || err);
    } finally {
      isLoading = false;
    }
  }

  function formatWeight(val) {
    if (val === null || val === undefined) return "0.000";
    return Number(val).toFixed(3);
  }
</script>

<div class="weight-field">
  <label class="field-label">{fieldName}</label>
  <div class="field-row">
    <input
      type="number"
      step="0.001"
      min="0"
      value={value}
      oninput={(e) => (value = parseFloat(e.target.value) || 0)}
      readonly={disabled}
      class="weight-input"
      class:editable={!disabled}
    />
    <button
      type="button"
      class="btn-tara"
      onclick={handleTara}
      disabled={isLoading}
      title="Tara (poner a cero)"
    >{isLoading ? "..." : "Tara"}</button>
    <button
      type="button"
      class="btn-leer"
      onclick={handleLeer}
      disabled={isLoading}
      title="Leer peso de la báscula"
    >{isLoading ? "..." : "Leer"}</button>
    {#if onReset}
      <button
        type="button"
        class="btn-reset-peso"
        onclick={onReset}
        title="Resetear este peso"
      >Reset</button>
    {/if}
  </div>
</div>

<style>
  .weight-field {
    margin-bottom: 12px;
  }

  .field-label {
    display: block;
    font-size: 14px;
    font-weight: 700;
    color: var(--text-secondary);
    margin-bottom: 6px;
  }

  .field-row {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .weight-input {
    width: 160px;
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 32px;
    font-weight: 700;
    text-align: right;
    font-family: "Courier New", monospace;
    outline: none;
    transition: border-color 0.2s;
  }

  .weight-input:focus {
    border-color: var(--accent);
  }

  .weight-input.editable {
    background: var(--bg-secondary);
    border-color: var(--warning);
  }

  .weight-input[readonly] {
    cursor: default;
    opacity: 0.85;
  }

  .btn-tara {
    padding: 10px 18px;
    border: none;
    border-radius: 8px;
    background: #3b82f6;
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
    white-space: nowrap;
  }

  .btn-tara:hover:not(:disabled) { background: #2563eb; }
  .btn-tara:disabled { opacity: 0.5; cursor: not-allowed; }

  .btn-leer {
    padding: 10px 18px;
    border: none;
    border-radius: 8px;
    background: #22c55e;
    color: white;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
    white-space: nowrap;
  }

  .btn-leer:hover:not(:disabled) {
    background: #16a34a;
  }

  .btn-leer:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-reset-peso {
    padding: 10px 14px;
    border: none;
    border-radius: 8px;
    background: #ef4444;
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
    white-space: nowrap;
  }

  .btn-reset-peso:hover { background: #dc2626; }
</style>
