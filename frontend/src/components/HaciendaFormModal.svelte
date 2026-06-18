<script>
  /**
   * HaciendaFormModal — Modal for creating and editing haciendas.
   * Props: show, mode ("create"|"edit"), hacienda (only edit), error, onClose, onSave.
   */
  let {
    show = false,
    mode = "create",
    hacienda = null,
    error = "",
    onClose = () => {},
    onSave = () => {},
  } = $props();

  let form = $state({ codigo: "", nombre: "" });
  let validationError = $state("");
  let submitting = $state(false);

  onMount(() => {
    if (show) {
      validationError = "";
      submitting = false;
      if (mode === "edit" && hacienda) {
        form = {
          codigo: hacienda.codigo || "",
          nombre: hacienda.nombre || "",
        };
      } else {
        form = { codigo: "", nombre: "" };
      }
    }
  });

  function validate() {
    if (!form.codigo.trim()) return "El código es requerido.";
    if (form.codigo.trim().length > 8) return "El código debe tener máximo 8 caracteres.";
    if (!form.nombre.trim()) return "El nombre es requerido.";
    if (form.nombre.trim().length > 255) return "El nombre debe tener máximo 255 caracteres.";
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
    onSave({
      codigo: form.codigo.trim(),
      nombre: form.nombre.trim(),
    });
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
        <h3>{mode === "create" ? "Nueva Hacienda" : "Editar Hacienda"}</h3>
        <button class="btn-close" onclick={onClose} aria-label="Cerrar">&times;</button>
      </div>

      {#if validationError || error}
        <div class="modal-error">{validationError || error}</div>
      {/if}

      <div class="modal-body">
        <label>
          Código
          <input type="text" bind:value={form.codigo} placeholder="Código (máx. 8 caracteres)" maxlength="8" />
        </label>
        <label>
          Nombre
          <input type="text" bind:value={form.nombre} placeholder="Nombre (máx. 255 caracteres)" maxlength="255" />
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
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .modal-header h3 {
    margin: 0;
    font-size: 18px;
    color: var(--text-primary);
  }

  .btn-close {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 22px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
  }

  .modal-error {
    background: rgba(255, 107, 107, 0.1);
    color: var(--error);
    border: 1px solid var(--error);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 16px;
    font-size: 13px;
  }

  .modal-body {
    display: flex;
    flex-direction: column;
    gap: 14px;
    margin-bottom: 24px;
  }

  .modal-body label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 13px;
    color: var(--text-secondary);
  }

  .modal-body input {
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 14px;
  }

  .modal-body input:focus {
    outline: none;
    border-color: var(--accent);
  }

  .modal-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .btn-cancel {
    padding: 10px 20px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-cancel:hover:not(:disabled) {
    background: var(--bg-input);
  }

  .btn-confirm {
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

  .btn-confirm:hover:not(:disabled) {
    background: var(--accent-hover);
  }

  .btn-confirm:disabled,
  .btn-cancel:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
