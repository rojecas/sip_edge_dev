<script>
  /**
   * NotesField — Collapsible textarea for operator notes.
   * Props: bind:notas (string), label (string, default "Notas").
   */
  let { notas = $bindable(""), label = "Notas" } = $props();
  let expanded = $state(false);

  function toggle() {
    expanded = !expanded;
  }

  function summaryText() {
    const trimmed = (notas || "").trim();
    if (!trimmed) return "";
    return trimmed.length > 50 ? trimmed.substring(0, 50) + "..." : trimmed;
  }
</script>

<div class="notes-field">
  <button
    type="button"
    class="notes-toggle"
    onclick={toggle}
    aria-expanded={expanded}
  >
    <span class="toggle-icon">{expanded ? "▼" : "▶"}</span>
    <span class="toggle-label">{label}</span>
    {#if !expanded && notas}
      <span class="toggle-summary">{summaryText()}</span>
    {/if}
  </button>

  {#if expanded}
    <div class="notes-body">
      <textarea
        bind:value={notas}
        placeholder="Observaciones sobre la muestra..."
        rows="3"
        class="notes-textarea"
      ></textarea>
    </div>
  {/if}
</div>

<style>
  .notes-field {
    margin-top: 8px;
    width: 100%;
  }

  .notes-toggle {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-secondary);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s;
  }

  .notes-toggle:hover {
    background: var(--bg-secondary);
    border-color: var(--accent);
  }

  .toggle-icon {
    font-size: 10px;
    width: 16px;
    text-align: center;
    flex-shrink: 0;
  }

  .toggle-label {
    flex-shrink: 0;
  }

  .toggle-summary {
    color: var(--text-secondary);
    font-weight: 400;
    font-style: italic;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    opacity: 0.7;
  }

  .notes-body {
    margin-top: 4px;
    animation: slideDown 0.2s ease;
  }

  .notes-textarea {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 14px;
    font-family: inherit;
    resize: vertical;
    min-height: 60px;
    outline: none;
    transition: border-color 0.2s;
    box-sizing: border-box;
  }

  .notes-textarea:focus {
    border-color: var(--accent);
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      max-height: 0;
    }
    to {
      opacity: 1;
      max-height: 200px;
    }
  }
</style>
