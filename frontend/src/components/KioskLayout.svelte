<script>
  /**
   * KioskLayout — Layout for operator views.
   * Header: username (left) + LogoutButton (right), EmergencyBanner (top).
   * Slot for child content (/kiosco or /kiosco/historial).
   */
  import { authStore } from "../stores/auth.js";
  import { navigate } from "../lib/router.js";
  import LogoutButton from "./LogoutButton.svelte";
  import EmergencyBanner from "./EmergencyBanner.svelte";

  let { children } = $props();

  function goToKiosk() {
    navigate("/kiosco");
  }

  function goToHistory() {
    navigate("/kiosco/historial");
  }
</script>

<div class="kiosk-layout">
  <EmergencyBanner />

  <header class="kiosk-header">
    <div class="header-left">
      <span class="user-info">
        {$authStore.username || "Operador"}
        <span class="role-badge">operador</span>
      </span>
    </div>
    <nav class="header-nav">
      <button class="nav-btn" onclick={goToKiosk}>Pesaje</button>
      <button
        class="nav-btn"
        onclick={goToHistory}
      >Historial</button>
    </nav>
    <div class="header-right">
      <LogoutButton />
    </div>
  </header>

  <main class="kiosk-main">
    {@render children?.()}
  </main>
</div>

<style>
  .kiosk-layout {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary);
  }

  .kiosk-header {
    display: flex;
    align-items: center;
    padding: 12px 24px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    gap: 24px;
  }

  .header-left {
    flex-shrink: 0;
  }

  .user-info {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .role-badge {
    display: inline-block;
    margin-left: 8px;
    padding: 2px 10px;
    border-radius: 12px;
    background: var(--bg-input);
    font-size: 12px;
    font-weight: 400;
    color: var(--text-secondary);
  }

  .header-nav {
    display: flex;
    gap: 8px;
  }

  .nav-btn {
    padding: 8px 16px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .nav-btn:hover {
    background: var(--bg-input);
    color: var(--text-primary);
  }

  .header-right {
    margin-left: auto;
  }

  /* Override LogoutButton positioning in this context */
  .header-right :global(.logout-btn) {
    position: static;
  }

  .kiosk-main {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
  }
</style>
