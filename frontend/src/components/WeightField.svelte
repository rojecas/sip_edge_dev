<script>
  /**
   * WeightField — Reusable weight input field with Tara/Leer buttons.
   * Props: fieldName, bind:value, disabled (true when emergency mode active = editable).
   * When disabled=true (normal mode), field is readonly — only updated via Tara/Leer.
   * When disabled=false (emergency mode), field is editable manually.
   */
  import { scaleStore } from "../lib/ws.js";

  let {
    fieldName = "",
    value = 0,
    disabled = true,
    onTara = () => {},
    onLeer = () => {},
  } = $props();

  function handleTara() {
    value = 0;
    onTara?.();
  }

  function handleLeer() {
    if (scaleStore.connected) {
      value = scaleStore.net_weight;
      onLeer?.();
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
      title="Tara (poner a cero)"
    >Tara</button>
    <button
      type="button"
      class="btn-leer"
      onclick={handleLeer}
      disabled={!scaleStore.connected}
      title="Leer peso de la báscula"
    >Leer</button>
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
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-secondary);
    color: var(--warning);
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
    white-space: nowrap;
  }

  .btn-tara:hover {
    background: var(--bg-input);
  }

  .btn-leer {
    padding: 10px 18px;
    border: none;
    border-radius: 8px;
    background: var(--accent);
    color: white;
    font-size: 14px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
    white-space: nowrap;
  }

  .btn-leer:hover:not(:disabled) {
    background: var(--accent-hover);
  }

  .btn-leer:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
