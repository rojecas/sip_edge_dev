<script>
  /**
   * AuthModal — Login modal with user/password fields.
   * Shows on app load if no JWT in localStorage.
   * Includes "Olvidó su contraseña" link that opens ResetPinModal.
   */
  import { api, ApiError } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";
  import { authStore } from "../stores/auth.svelte.js";
  import { navigate } from "../lib/router.svelte.js";
  import ResetPinModal from "./ResetPinModal.svelte";

  let username = $state("");
  let password = $state("");
  let errorMessage = $state("");
  let isLoading = $state(false);
  let showResetPin = $state(false);

  let derived = $derived.by(() => {
    return {
      canSubmit: username.trim() !== "" && password.trim() !== "",
    };
  });

  async function handleLogin() {
    if (!derived.canSubmit || isLoading) return;
    isLoading = true;
    errorMessage = "";

    try {
      const data = await api.post(ENDPOINTS.LOGIN, {
        username: username.trim(),
        password: password,
      });
      authStore.login(data.access_token, data.role, username.trim());
      if (data.role === "admin") {
        navigate("/admin");
      } else {
        navigate("/kiosco");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401 || err.status === 403) {
          errorMessage = "Usuario o contraseña incorrectos";
        } else {
          errorMessage = err.message;
        }
      } else {
        errorMessage = "Error de conexión";
      }
    } finally {
      isLoading = false;
    }
  }

  function handleKeydown(e) {
    if (e.key === "Enter" && derived.canSubmit && !isLoading) {
      handleLogin();
    }
  }

  function openResetPin() {
    showResetPin = true;
  }

  function closeResetPin() {
    showResetPin = false;
  }
</script>

<div class="modal-overlay">
  <div class="modal-container">
    <h1 class="modal-title">SIP-Edge</h1>
    <p class="modal-subtitle">Sistema Inteligente de Pesaje</p>

    <form onsubmit={(e) => e.preventDefault()} class="login-form">
      <div class="field">
        <label for="username">Usuario</label>
        <input
          id="username"
          type="text"
          autocomplete="username"
          bind:value={username}
          onkeydown={handleKeydown}
          disabled={isLoading}
          placeholder="Ingrese su usuario"
        />
      </div>

      <div class="field">
        <label for="password">Contraseña</label>
        <input
          id="password"
          type="password"
          autocomplete="current-password"
          bind:value={password}
          onkeydown={handleKeydown}
          disabled={isLoading}
          placeholder="Ingrese su contraseña"
        />
      </div>

      {#if errorMessage}
        <p class="error-message">{errorMessage}</p>
      {/if}

      <button
        type="button"
        class="btn-primary"
        onclick={handleLogin}
        disabled={!derived.canSubmit || isLoading}
      >
        {isLoading ? "Iniciando..." : "Iniciar Sesión"}
      </button>

      <button type="button" class="btn-link" onclick={openResetPin}>
        ¿Olvidó su contraseña?
      </button>
    </form>
  </div>
</div>

{#if showResetPin}
  <ResetPinModal onclose={closeResetPin} />
{/if}

<style>
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 40px;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  }

  .modal-title {
    margin: 0;
    font-size: 28px;
    color: var(--accent);
    text-align: center;
  }

  .modal-subtitle {
    margin: 8px 0 32px;
    font-size: 14px;
    color: var(--text-secondary);
    text-align: center;
  }

  .login-form {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 6px;
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
    transition: border-color 0.2s;
  }

  .field input:focus {
    border-color: var(--accent);
  }

  .field input::placeholder {
    color: var(--text-secondary);
    opacity: 0.6;
  }

  .error-message {
    color: var(--error);
    font-size: 14px;
    margin: 0;
    padding: 8px 12px;
    background: rgba(255, 107, 107, 0.1);
    border-radius: 8px;
  }

  .btn-primary {
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

  .btn-link {
    background: none;
    border: none;
    color: var(--accent);
    font-size: 14px;
    cursor: pointer;
    padding: 4px;
    text-decoration: underline;
  }

  .btn-link:hover {
    color: var(--accent-hover);
  }
</style>
