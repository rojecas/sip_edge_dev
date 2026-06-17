<script>
  /**
   * SuerteFormModal — Modal for creating and editing suertes.
   * Props: show, mode ("create"|"edit"), suerte (only edit), haciendaId,
   *        haciendas (list for dropdown), error, onClose, onSave.
   */
  let {
    show = false,
    mode = "create",
    suerte = null,
    haciendaId = null,
    haciendas = [],
    error = "",
    onClose = () => {},
    onSave = () => {},
  } = $props();

  let form = $state({ hacienda_id: 0, codigo_suerte: "" });
  let validationError = $state("");
  let submitting = $state(false);

  $effect(() => {
    if (show) {
      validationError = "";
      submitting = false;
      if (mode === "edit" && suerte) {
        form = {
          hacienda_id: suerte.hacienda_id || haciendaId || 0,
          codigo_suerte: suerte.codigo_suerte || "",
        };
      } else {
        form = {
          hacienda_id: haciendaId || 0,
          codigo_suerte: "",
        };
      }
    }
  });

  function validate() {
    if (!form.codigo_suerte.trim()) return "El código de suerte es requerido.";
    if (form.codigo_suerte.trim().length > 4) return "El código debe tener máximo 4 caracteres.";
    return "";
  }

  function handleSubmit() {
    const vErr = validate();
    if (vErr) {
      validationError = vErr;
      return;
    }
    validationError = "";
    submitting = true;
    const payload = mode === "create"
      ? {
          hacienda_id: form.hacienda_id,
          codigo_suerte: form.codigo_suerte.trim(),
        }
      : {
          codigo_suerte: form.codigo_suerte.trim(),
        };
    onSave(payload);
  }

  function handleOverlayClick(e) {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }
</script>

{#if show}
  <div class="modal-overlay" onclick={handleOverlayClick}>
    <div class="modal-container">
      <div class="modal-header">
        <h3>{mode === "create" ? "Nueva Suerte" : "Editar Suerte"}</h3>
        <button class="btn-close" onclick={onClose} aria-label="Cerrar">&times;</button>
      </div>

      {#if validationError || error}
        <div class="modal-error">{validationError || error}</div>
      {/if}

      <div class="modal-body">
        {#if mode === "create"}
          <label>
            Hacienda
            <select bind:value={form.hacienda_id}>
              {#each haciendas as h}
                <option value={h.id}>{h.nombre} ({h.codigo})</option>
              {/each}
            </select>
          </label>
        {:else}
          <label>
            Hacienda
            <input type="text" value={suerte?.hacienda_nombre || `ID ${form.hacienda_id}`} disabled />
          </label>
        {/if}

        <label>
          Código Suerte
          <input type="text" bind:value={form.codigo_suerte} placeholder="Código (máx. 4 caracteres)" maxlength="4" />
        </label>
      </div>

      <div class="modal-actions">
        <button class="btn-cancel" onclick={onClose} disabled={submitting}>Cancelar</button>
        <button class="btn-confirm" onclick={handleSubmit} disabled={submitting}>
          {submitting ? "Guardando..." : "Guardar"}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
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
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 20px;
  }
  .modal-header h3 { margin: 0; font-size: 18px; color: var(--text-primary); }
  .btn-close { background: none; border: none; color: var(--text-secondary); font-size: 22px; cursor: pointer; padding: 0 4px; line-height: 1; }
  .modal-error {
    background: rgba(255, 107, 107, 0.1); color: var(--error);
    border: 1px solid var(--error); border-radius: 8px;
    padding: 10px 14px; margin-bottom: 16px; font-size: 13px;
  }
  .modal-body { display: flex; flex-direction: column; gap: 14px; margin-bottom: 24px; }
  .modal-body label { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--text-secondary); }
  .modal-body input, .modal-body select {
    padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px;
    background: var(--bg-input); color: var(--text-primary); font-size: 14px;
  }
  .modal-body input:focus, .modal-body select:focus { outline: none; border-color: var(--accent); }
  .modal-actions { display: flex; gap: 12px; justify-content: flex-end; }
  .btn-cancel {
    padding: 10px 20px; border: 1px solid var(--border); border-radius: 8px;
    background: transparent; color: var(--text-secondary); font-size: 14px;
    cursor: pointer; transition: background 0.2s;
  }
  .btn-cancel:hover:not(:disabled) { background: var(--bg-input); }
  .btn-confirm {
    padding: 10px 20px; border: none; border-radius: 8px;
    background: var(--accent); color: white; font-size: 14px; font-weight: 600;
    cursor: pointer; transition: background 0.2s;
  }
  .btn-confirm:hover:not(:disabled) { background: var(--accent-hover); }
  .btn-confirm:disabled, .btn-cancel:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
