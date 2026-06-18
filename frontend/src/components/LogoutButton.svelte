<script>
  /**
   * LogoutButton — Always visible in top-right corner.
   * Shows ConfirmModal before logging out.
   */
  import { authStore } from "../stores/auth.svelte.js";
  import { navigate } from "../lib/router.svelte.js";
  import ConfirmModal from "./ConfirmModal.svelte";

  let showConfirm = $state(false);

  function handleLogout() {
    showConfirm = true;
  }

  function confirmLogout() {
    authStore.logout();
    showConfirm = false;
    navigate("/");
  }

  function cancelLogout() {
    showConfirm = false;
  }
</script>

<button class="logout-btn" onclick={handleLogout} title="Cerrar sesión">
  Cerrar sesión
</button>

{#if showConfirm}
  <ConfirmModal
    show={showConfirm}
    title="Cerrar Sesión"
    message="¿Está seguro de cerrar sesión?"
    confirmText="Cerrar Sesión"
    cancelText="Cancelar"
    onConfirm={confirmLogout}
    onCancel={cancelLogout}
  />
{/if}

<style>
  .logout-btn {
    position: fixed;
    top: 16px;
    right: 16px;
    z-index: 500;
    padding: 10px 20px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-secondary);
    color: var(--text-primary);
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s;
  }

  .logout-btn:hover {
    background: var(--accent);
    border-color: var(--accent);
    color: white;
  }
</style>
