<script>
  /**
   * InactivityGuard — Detects real user activity via DOM events and refreshes
   * the JWT token periodically. Logs out when backend session expires.
   *
   * Fixes regression bug #40: the backend middleware excludes polling paths
   * (/api/auth/status, /api/emergency/status) from updating last_activity.
   * Plain text inputs (Tractomula, vagon, guia) don't trigger API calls,
   * so they never update last_activity. This guard now calls refreshToken()
   * on DOM events to keep the session alive for ANY user interaction.
   */
  import { onMount } from "svelte";
  import { authStore } from "../stores/auth.js";
  import { CONFIG } from "../lib/constants.js";

  let logoutMessage = $state("");
  let pollTimer = null;
  let refreshTimer = null;
  let lastDomActivity = Date.now() / 1000;

  /** Debounced refresh: call refreshToken on DOM events, max once every 60s. */
  let refreshPending = false;
  function scheduleRefresh() {
    lastDomActivity = Date.now() / 1000;
    if (refreshPending) return;
    refreshPending = true;
    setTimeout(async () => {
      refreshPending = false;
      if (!authStore.isAuthenticated) return;
      // Only refresh if there was recent DOM activity (within last 90s)
      const elapsed = (Date.now() / 1000) - lastDomActivity;
      if (elapsed < 90) {
        try {
          await authStore.refreshToken();
        } catch {
          // Network error — ignore, retry next cycle
        }
      }
    }, 1000); // debounce 1s to batch rapid events
  }

  /** Activity event handler — attached to document-level events. */
  function onDomActivity() {
    scheduleRefresh();
  }

  /** Poll backend session status as safety net. */
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
    const pollIntervalMs = CONFIG.INACTIVITY_CHECK_INTERVAL_MS;
    pollTimer = setInterval(checkSession, pollIntervalMs);

    // Periodic token refresh (every REFRESH_INTERVAL_MS = 120s) as backup
    refreshTimer = setInterval(async () => {
      if (!authStore.isAuthenticated) return;
      try { await authStore.refreshToken(); } catch { /* ignore */ }
    }, CONFIG.REFRESH_INTERVAL_MS);

    // DOM event listeners for real user activity
    const events = ["mousedown", "keydown", "touchstart", "mousemove"];
    events.forEach(evt => document.addEventListener(evt, onDomActivity, { passive: true }));

    return () => {
      clearInterval(pollTimer);
      clearInterval(refreshTimer);
      events.forEach(evt => document.removeEventListener(evt, onDomActivity));
    };
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
