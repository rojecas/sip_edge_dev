<script>
  /**
   * InactivityGuard — Polls backend session status. Logs out when session expires.
   */
  import { onMount, onDestroy } from "svelte";
  import { authStore } from "../stores/auth.js";

  let logoutMessage = $state("");
  let timer = null;

  function getPollIntervalSeconds() {
    const payload = authStore.jwtPayload;
    const timeout = (payload && payload.session_timeout_minutes) ? payload.session_timeout_minutes : 30;
    return Math.min(timeout * 20, 30); // 1/3 of timeout, max 30s
  }

  async function checkSession() {
    if (!authStore.isAuthenticated) return;
    const token = authStore.token;
    if (!token) return;
    try {
      const resp = await fetch("/api/auth/status", {
        headers: { "Authorization": "Bearer " + token }
      });
      if (!resp.ok || !(await resp.json()).valid) {
        logoutMessage = "Sesion expirada por inactividad";
        authStore.logout();
      }
    } catch {
      // Network error — ignore, retry next poll
    }
  }

  onMount(() => {
    const intervalMs = getPollIntervalSeconds() * 1000;
    timer = setInterval(checkSession, intervalMs);
    return () => clearInterval(timer);
  });
</script>

{#if logoutMessage}
  <div class="expired-banner">{logoutMessage}</div>
{/if}

<style>
  .expired-banner {
    position: fixed; top: 0; left: 0; right: 0; z-index: 3000;
    padding: 14px; text-align: center;
    background: var(--error); color: white;
    font-size: 16px; font-weight: 600;
  }
</style>
