<script>
  /**
   * InactivityGuard — Monitors JWT iat and calls logout if session expired.
   * Mounted when user is authenticated.
   */
  import { onMount, onDestroy } from "svelte";
  import { authStore } from "../stores/auth.js";
  import { checkInactivity } from "../lib/inactivity.js";
  import { CONFIG } from "../lib/constants.js";

  let logoutMessage = $state("");

  let timer = null;

  function checkSession() {
    const payload = authStore.jwtPayload;
    if (!payload) {
      authStore.logout();
      return;
    }
    const timeout = authStore.getSessionTimeout(payload);
    if (checkInactivity(payload, timeout)) {
      logoutMessage = "Sesión expirada por inactividad";
      authStore.logout();
    }
  }

  onMount(() => {
    checkSession();
    timer = setInterval(checkSession, CONFIG.INACTIVITY_CHECK_INTERVAL_MS);
  });

  onDestroy(() => {
    if (timer) {
      clearInterval(timer);
    }
  });
</script>

{#if logoutMessage}
  <div class="expired-banner">
    {logoutMessage}
  </div>
{/if}

<style>
  .expired-banner {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 3000;
    padding: 14px;
    text-align: center;
    background: var(--error);
    color: white;
    font-size: 16px;
    font-weight: 600;
  }
</style>
