<script>
  import { onMount } from "svelte";
  /**
   * UserFormModal — Modal for creating and editing users.
   * Props: show, mode ("create"|"edit"), user (only edit), error, onClose, onSave.
   * onSave receives the payload object. Parent should handle API call and
   * pass back errors via the `error` prop.
   */
  let {
    show = false,
    mode = "create",
    user = null,
    error = "",
    onClose = () => {},
    onSave = () => {},
  } = $props();

  const ROLES = ["admin", "operator", "corresponsal"];

  let form = $state({
    username: "",
    password: "",
    full_name: "",
    document: "",
    role: "operator",
    is_active: true,
    new_password: "",
  });

  let validationError = $state("");
  let submitting = $state(false);

  // Reset form when modal opens (reactive to show)
  $effect(() => {
    if (show) {
      validationError = "";
      submitting = false;
      if (mode === "edit" && user) {
        form = {
          username: user.username || "",
          password: "",
          full_name: user.full_name || "",
          document: user.document || "",
          role: user.role || "operator",
          is_active: user.is_active !== undefined ? user.is_active : true,
          new_password: "",
        };
      } else {
        form = {
          username: "",
          password: "",
          full_name: "",
          document: "",
          role: "operator",
          is_active: true,
          new_password: "",
        };
      }
    }
  });

  function validate() {
    if (mode === "create") {
      if (!form.username.trim()) return "El usuario es requerido.";
      if (!form.password.trim()) return "La contraseña es requerida.";
    }
    if (!form.full_name.trim()) return "El nombre completo es requerido.";
    return "";
  }

  async function handleSubmit() {
    const vErr = validate();
    if (vErr) {
      validationError = vErr;
      return;
    }
    validationError = "";
    submitting = true;
    const payload = mode === "create"
      ? {
          username: form.username.trim(),
          password: form.password,
          full_name: form.full_name.trim(),
          document: form.document.trim() || null,
          role: form.role,
        }
      : {
          full_name: form.full_name.trim(),
          document: form.document.trim() || null,
          role: form.role,
          is_active: form.is_active,
          ...(form.new_password.trim() ? { password: form.new_password } : {}),
        };
    await onSave(payload);
    submitting = false;
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
        <h3>{mode === "create" ? "Nuevo Usuario" : "Editar Usuario"}</h3>
        <button class="btn-close" onclick={onClose} aria-label="Cerrar">&times;</button>
      </div>

      {#if validationError || error}
        <div class="modal-error">{validationError || error}</div>
      {/if}

      <div class="modal-body">
        {#if mode === "create"}
          <label>
            Usuario
            <input type="text" bind:value={form.username} placeholder="Nombre de usuario" />
          </label>
          <label>
            Contraseña
            <input type="password" bind:value={form.password} placeholder="Contraseña" />
          </label>
        {:else}
          <div class="info-field">
            <span class="info-label">Usuario:</span>
            <span class="info-value">{user?.username || "—"}</span>
          </div>
        {/if}

        <label>
          Nombre Completo
          <input type="text" bind:value={form.full_name} placeholder="Nombre completo" />
        </label>

        <label>
          Documento
          <input type="text" bind:value={form.document} placeholder="Documento (opcional)" />
        </label>

        <label>
          Rol
          <select bind:value={form.role}>
            {#each ROLES as r}
              <option value={r}>{r}</option>
            {/each}
          </select>
        </label>

        {#if mode === "edit"}
          <label class="checkbox-label">
            <input type="checkbox" bind:checked={form.is_active} />
            Activo
          </label>

          <label>
            Nueva Contraseña (opcional)
            <input type="password" bind:value={form.new_password} placeholder="Dejar vacío para no cambiar" />
          </label>
        {/if}
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
    max-height: 90vh;
    overflow-y: auto;
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

  .checkbox-label {
    flex-direction: row !important;
    align-items: center;
    gap: 8px;
  }

  .checkbox-label input[type="checkbox"] {
    width: 16px;
    height: 16px;
    accent-color: var(--accent);
  }

  .info-field {
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    display: flex;
    gap: 8px;
    font-size: 14px;
  }

  .info-label {
    color: var(--text-secondary);
    font-weight: 500;
  }

  .info-value {
    color: var(--text-primary);
    font-weight: 600;
  }

  .modal-body input,
  .modal-body select {
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 14px;
  }

  .modal-body input:focus,
  .modal-body select:focus {
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
