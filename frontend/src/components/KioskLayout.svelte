<script>
  /**
   * KioskLayout — Layout for operator views.
   * Header: username + icon (left), nav Pesaje/Historial, app name, logout (right).
   */
  import { authStore } from "../stores/auth.js";
  import { navigate } from "../lib/router.js";
  import LogoutButton from "./LogoutButton.svelte";
  import EmergencyBanner from "./EmergencyBanner.svelte";

  let { children } = $props();

  let currentRoute = $state(window.location.hash.slice(1) || "/");

  $effect(() => {
    const handler = () => {
      currentRoute = window.location.hash.slice(1) || "/";
    };
    window.addEventListener("hashchange", handler);
    return () => window.removeEventListener("hashchange", handler);
  });

  function goToPesaje() {
    navigate("/kiosco");
  }

  function goToHistorial() {
    navigate("/kiosco/historial");
  }
</script>

<div class="kiosk-layout">
  <EmergencyBanner />

  <header class="kiosk-header">
    <div class="header-left">
      <span class="user-info">
        <svg class="user-icon" width="24" height="24" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
          <path style="fill:#427794;stroke:#2A424F" d="M 22,43 C 18,48 6.5,45 4.2,56 2,62 2,81 14,79 13,64 12,57 12,57 c 0,0 1,14 2,21 9,4 24,4 35,-1 0,-8 -1,-13 0,-18 0,-5 0,19 0,19 0,0 6,2 8,-5 3,-10 5,-24 -9,-28 -9,-1 -7,-2 -8,-2 -2,0 -18,0 -18,0 z"/>
          <path style="fill:#C29B82;stroke:#693311" d="m 23,38 c 0,0 1,3 -1,5 3,4 11,8 18,0 -1,-2 -1,-2 -1,-5 0,0 -16,0 -16,0 z"/>
          <path style="fill:#CDA68E;stroke:#693311" d="M 31,42 C 17,42 7.6,4.8 31,4.2 55,4.1 44,42 31,42 z"/>
          <path style="fill:#553932;stroke:#311710" d="M 17,26 C 14,16 14,3.2 31,2.4 44,3.1 49,15 44,26 44,21 45,19 43,16 39,15 33,16 28,11 27,15 15,13 17,26 z"/>
          <path style="fill:#5F3E20;stroke:#311710" d="m 45,65 c 5,-8 0,-25 3,-31 3,-10 7,-16 16,-16 10,0 16,8 20,17 1,2 0,6 2,11 1,4 -1,8 -1,10 0,5 -1,3 2,9 -5,13 -34,10 -42,0 z"/>
          <path style="fill:#D8933B;stroke:#2A424F" d="m 58,60 c -5,5 -18,3 -20,13 -2,6 -1,25 11,24 -1,-16 -3,-23 -3,-23 0,0 2,15 3,21 9,5 23,5 35,-1 0,-6 -1,-13 0,-18 1,-5 0,20 0,20 0,0 7,1 9,-6 2,-9 4,-22 -7,-25 -9,-3 -10,-5 -12,-5 -1,0 -16,0 -16,0 z"/>
          <path style="fill:#DEB89F;stroke:#693311" d="m 58,54 c 0,0 1,3 0,7 3,3 10,8 16,0 -1,-4 -1,-4 -1,-7 0,0 -15,0 -15,0 z"/>
          <path style="fill:#DBBFA8;stroke:#693311" d="M 66,59 C 52,59 43,21 66,20 86,21 79,59 66,59 z"/>
          <path style="fill:#5F3E20" d="m 63,27 c -3,5 -7,8 -12,9 -4,1 2,-17 13,-17 5,0 13,3 15,15 -6,1 -14,-5 -16,-7"/>
        </svg>
        {$authStore && $authStore.username ? $authStore.username : "Operador"}
        <span class="role-badge">operador</span>
      </span>
    </div>
    <nav class="header-nav">
      <button
        class="nav-btn"
        class:active={currentRoute === "/kiosco"}
        onclick={goToPesaje}
      >Pesaje</button>
      <button
        class="nav-btn"
        class:active={currentRoute === "/kiosco/historial"}
        onclick={goToHistorial}
      >Historial</button>
    </nav>
    <div class="header-center">
      <span class="app-name">Sip-Edge</span>
    </div>
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
    position: relative;
  }

  .header-left {
    flex-shrink: 0;
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .user-icon {
    flex-shrink: 0;
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
    margin-left: 32px;
  }

  .nav-btn {
    padding: 8px 20px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }

  .nav-btn:hover {
    background: var(--bg-input);
    color: var(--text-primary);
  }

  .nav-btn.active {
    background: var(--bg-input);
    border-color: var(--bg-input);
    color: var(--text-primary);
  }

  .header-center {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
  }

  .app-name {
    font-size: 38px;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 1px;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
  }

  .header-right {
    flex-shrink: 0;
    margin-left: auto;
  }

  .header-right :global(.logout-btn) {
    position: static;
  }

  .kiosk-main {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
  }
</style>
