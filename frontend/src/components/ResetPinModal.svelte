<script>
  /**
   * ResetPinModal — "Olvidó su contraseña" step 1.
   * User enters username + 4-digit PIN from SMS.
   * On success, opens ResetPasswordModal with reset_token.
   */
  import { api, ApiError } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";
  import ResetPasswordModal from "./ResetPasswordModal.svelte";

  let { onclose } = $props();

  let username = $state("");
  let pin = $state("");
  let errorMessage = $state("");
  let isLoading = $state(false);
  let showPasswordModal = $state(false);
  let resetToken = $state("");

  let canSubmit = $derived(
    username.trim() !== "" && pin.trim().length === 4 && !isLoading
  );

  async function handleVerify() {
    if (!canSubmit) return;
    isLoading = true;
    errorMessage = "";

    try {
      const data = await api.post(ENDPOINTS.VERIFY_RESET_PIN, {
        username: username.trim(),
        pin: pin.trim(),
      });
      resetToken = data.reset_token || "";
      showPasswordModal = true;
    } catch (err) {
      if (err instanceof ApiError) {
        errorMessage = "PIN inválido o expirado";
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

  function handlePinInput(e) {
    // Only allow digits, max 4
    const val = e.target.value.replace(/\D/g, "").slice(0, 4);
    pin = val;
  }
</script>

{#if showPasswordModal}
  <ResetPasswordModal
    resetToken={resetToken}
    onclose={onclose}
  />
{:else}
  <div class="modal-overlay" onclick={handleOverlayClick}>
    <div class="modal-container">
      <div class="modal-header">
        <h2>Restablecer Contraseña</h2>
        <button class="btn-close" onclick={handleClose} aria-label="Cerrar">&times;</button>
      </div>

      <p class="modal-desc">
        Ingrese su usuario y el PIN de 4 dígitos enviado por SMS.
      </p>

      <form onsubmit={(e) => e.preventDefault()}>
        <div class="field">
          <label for="reset-user">Usuario</label>
          <input
            id="reset-user"
            type="text"
            bind:value={username}
            disabled={isLoading}
            placeholder="Su nombre de usuario"
          />
        </div>

        <div class="field">
          <label for="reset-pin">PIN (4 dígitos)</label>
          <input
            id="reset-pin"
            type="text"
            inputmode="numeric"
            maxlength="4"
            value={pin}
            oninput={handlePinInput}
            disabled={isLoading}
            placeholder="0000"
            class="pin-input"
          />
        </div>

        {#if errorMessage}
          <p class="error-message">{errorMessage}</p>
        {/if}

        <button
          type="button"
          class="btn-primary"
          onclick={handleVerify}
          disabled={!canSubmit}
        >
          {isLoading ? "Verificando..." : "Verificar PIN"}
        </button>
      </form>
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
    z-index: 1100;
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

  .modal-desc {
    margin: 0 0 20px;
    font-size: 14px;
    color: var(--text-secondary);
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

  .pin-input {
    letter-spacing: 8px;
    text-align: center;
    font-size: 24px !important;
  }

  .error-message {
    color: var(--error);
    font-size: 14px;
    margin: 0 0 16px;
    padding: 8px 12px;
    background: rgba(255, 107, 107, 0.1);
    border-radius: 8px;
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
