<script>
  /**
   * ResetPasswordModal — "Olvidó su contraseña" step 2.
   * User enters new password + confirmation.
   * Sends POST /api/auth/complete-reset.
   * On success, shows message and closes after 2 seconds.
   */
  import { api, ApiError } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";

  let { resetToken, onclose } = $props();

  let newPassword = $state("");
  let confirmPassword = $state("");
  let errorMessage = $state("");
  let isLoading = $state(false);
  let successMessage = $state("");

  let canSubmit = $derived(
    newPassword.length >= 1 && confirmPassword.length >= 1 && !isLoading
  );

  async function handleComplete() {
    if (!canSubmit) return;
    if (newPassword !== confirmPassword) {
      errorMessage = "Las contraseñas no coinciden";
      return;
    }
    isLoading = true;
    errorMessage = "";

    try {
      await api.post(ENDPOINTS.COMPLETE_RESET, {
        reset_token: resetToken,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      successMessage = "Contraseña cambiada exitosamente.";
      setTimeout(() => {
        onclose?.();
      }, 2000);
    } catch (err) {
      if (err instanceof ApiError) {
        errorMessage = err.message;
      } else {
        errorMessage = "Error de conexión";
      }
    } finally {
      isLoading = false;
    }
  }

  function handleClose() {
    onclose?.();
  }

  function handleOverlayClick(e) {
    if (e.target === e.currentTarget) {
      handleClose();
    }
  }
</script>

<div class="modal-overlay" onclick={handleOverlayClick}>
  <div class="modal-container">
    <div class="modal-header">
      <h2>Nueva Contraseña</h2>
      <button class="btn-close" onclick={handleClose} aria-label="Cerrar">&times;</button>
    </div>

    {#if successMessage}
      <p class="success-message">{successMessage}</p>
    {:else}
      <form onsubmit={(e) => e.preventDefault()}>
        <div class="field">
          <label for="new-password">Nueva Contraseña</label>
          <input
            id="new-password"
            type="password"
            bind:value={newPassword}
            disabled={isLoading}
            placeholder="Ingrese nueva contraseña"
          />
        </div>

        <div class="field">
          <label for="confirm-password">Confirmar Contraseña</label>
          <input
            id="confirm-password"
            type="password"
            bind:value={confirmPassword}
            disabled={isLoading}
            placeholder="Confirme la contraseña"
          />
        </div>

        {#if errorMessage}
          <p class="error-message">{errorMessage}</p>
        {/if}

        <button
          type="button"
          class="btn-primary"
          onclick={handleComplete}
          disabled={!canSubmit}
        >
          {isLoading ? "Cambiando..." : "Cambiar Contraseña"}
        </button>
      </form>
    {/if}
  </div>
</div>

<style>
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1200;
  }

  .modal-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 32px;
    width: 100%;
    max-width: 400px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .modal-header h2 {
    margin: 0;
    font-size: 20px;
    color: var(--text-primary);
  }

  .btn-close {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 24px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
  }

  .btn-close:hover {
    color: var(--text-primary);
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 16px;
  }

  .field label {
    font-size: 14px;
    color: var(--text-secondary);
    font-weight: 600;
  }

  .field input {
    padding: 12px 16px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 16px;
    outline: none;
  }

  .field input:focus {
    border-color: var(--accent);
  }

  .error-message {
    color: var(--error);
    font-size: 14px;
    margin: 0 0 16px;
    padding: 8px 12px;
    background: rgba(255, 107, 107, 0.1);
    border-radius: 8px;
  }

  .success-message {
    color: var(--success);
    font-size: 16px;
    text-align: center;
    padding: 24px 0;
  }

  .btn-primary {
    width: 100%;
    padding: 14px;
    border: none;
    border-radius: 8px;
    background: var(--accent);
    color: white;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-primary:hover:not(:disabled) {
    background: var(--accent-hover);
  }

  .btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
