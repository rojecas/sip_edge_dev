<script>
  /**
   * EmergencyModal — Request emergency mode.
   * Loads admin supervisors list, shows dropdown + reason field.
   */
  import { onMount } from "svelte";
  import { api, ApiError } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";

  let { onclose } = $props();

  let admins = $state([]);
  let selectedAdminId = $state(null);
  let reason = $state("");
  let isLoading = $state(false);
  let isLoadingAdmins = $state(true);
  let errorMessage = $state("");
  let successMessage = $state("");

  onMount(() => {
    loadAdmins();
  });

  async function loadAdmins() {
    isLoadingAdmins = true;
    try {
      const data = await api.get(ENDPOINTS.EMERGENCY_ADMINS);
      admins = Array.isArray(data) ? data : (data.items || []);
    } catch {
      errorMessage = "Error al cargar supervisores";
    } finally {
      isLoadingAdmins = false;
    }
  }

  let canSubmit = $derived(
    selectedAdminId !== null && reason.trim() !== "" && !isLoading
  );

  async function handleSubmit() {
    if (!canSubmit) return;
    isLoading = true;
    errorMessage = "";

    try {
      await api.post(ENDPOINTS.EMERGENCY_REQUEST, {
        admin_id: selectedAdminId,
        reason: reason.trim(),
      });
      successMessage = "Solicitud enviada. Espere respuesta del supervisor.";
      setTimeout(() => {
        onclose?.();
      }, 2500);
    } catch (err) {
      if (err instanceof ApiError) {
        errorMessage = err.message;
      } else {
        errorMessage = "Error al enviar la solicitud";
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
      <h2>Solicitar Modo Manual</h2>
      <button class="btn-close" onclick={handleClose} aria-label="Cerrar">&times;</button>
    </div>

    {#if successMessage}
      <p class="success-message">{successMessage}</p>
    {:else}
      <form onsubmit={(e) => e.preventDefault()}>
        <div class="field">
          <label for="supervisor">Supervisor</label>
          {#if isLoadingAdmins}
            <p class="hint">Cargando supervisores...</p>
          {:else if admins.length === 0}
            <p class="hint">No hay supervisores disponibles</p>
          {:else}
            <select
              id="supervisor"
              bind:value={selectedAdminId}
              class="select-input"
            >
              <option value={null}>Seleccione un supervisor</option>
              {#each admins as admin}
                <option value={admin.id}>
                  {admin.full_name || admin.username || `Admin #${admin.id}`}
                </option>
              {/each}
            </select>
          {/if}
        </div>

        <div class="field">
          <label for="reason">Motivo</label>
          <textarea
            id="reason"
            bind:value={reason}
            disabled={isLoading}
            placeholder="Explique el motivo de la solicitud de modo manual"
            rows="3"
            class="textarea-input"
          ></textarea>
        </div>

        {#if errorMessage}
          <p class="error-message">{errorMessage}</p>
        {/if}

        <button
          type="button"
          class="btn-primary"
          onclick={handleSubmit}
          disabled={!canSubmit}
        >
          {isLoading ? "Enviando..." : "Enviar solicitud"}
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
    z-index: 1500;
  }

  .modal-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 32px;
    width: 100%;
    max-width: 460px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
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
    font-weight: 600;
    color: var(--text-secondary);
  }

  .select-input {
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 15px;
    outline: none;
    cursor: pointer;
  }

  .select-input:focus {
    border-color: var(--accent);
  }

  .textarea-input {
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 15px;
    outline: none;
    resize: vertical;
    font-family: inherit;
  }

  .textarea-input:focus {
    border-color: var(--accent);
  }

  .hint {
    font-size: 14px;
    color: var(--text-secondary);
    margin: 0;
    padding: 8px 0;
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
