<script>
  /**
   * AdminLayout — Layout for admin views.
   * Sidebar navigation (left) + header with LogoutButton + content slot.
   */
  import { authStore } from "../stores/auth.js";
  import { navigate } from "../lib/router.js";
  import { router } from "../lib/router.js";
  import LogoutButton from "./LogoutButton.svelte";
  import AboutModal from "./AboutModal.svelte";

  let { children } = $props();
  let showAbout = $state(false);

  let currentRoute = $derived($router);

  const links = [
    { route: "/admin", label: "Dashboard", icon: "📊" },
    { route: "/admin/config", label: "Configuración", icon: "⚙️" },
    { route: "/admin/usuarios", label: "Usuarios", icon: "👥" },
    { route: "/admin/haciendas", label: "Haciendas", icon: "🏠" },
    { route: "/admin/suertes", label: "Suertes", icon: "🌱" },
    { route: "/admin/reportes", label: "Reportes", icon: "📋" },
    { route: "/admin/anomalias", label: "Anomalías", icon: "⚠️" },
    { route: "/admin/agente", label: "Agente IA", icon: "🤖" },
    { route: "/admin/backup", label: "Backup", icon: "💾" },{ route: "/kiosco/historial", label: "Kiosko", icon: "🏭" },
  ];

  function goTo(route) {
    navigate(route);
  }
</script>

<div class="admin-layout">
  <aside class="sidebar">
    <div class="sidebar-header">
      <img src="/static/logo-mayaguez.png" alt="Mayagüez" class="sidebar-logo" width="64" height="64" />
      <span class="sidebar-title">SIP-Edge Admin</span>
    </div>
    <nav class="sidebar-nav">
      {#each links as link}
        <button
          class="sidebar-link"
          class:active={currentRoute === link.route}
          onclick={() => goTo(link.route)}
        >
          <span class="link-icon">{link.icon}</span>
          <span class="link-label">{link.label}</span>
        </button>
      {/each}
    </nav>
    <div class="sidebar-footer">
      <span class="sidebar-user">{$authStore && $authStore.username ? $authStore.username : "Admin"}</span>
      <span class="sidebar-role">admin</span>
    </div>
  </aside>

  <div class="admin-right">
    <header class="admin-header">
      <div class="header-left">
        <span class="user-info">
          {$authStore && $authStore.username ? $authStore.username : "Admin"}
          <span class="role-badge">admin</span>
        </span>
      </div>
      <div class="header-right">
        <button class="sidebar-about" onclick={() => showAbout = true} title="Acerca de">ⓘ</button>
      <LogoutButton />
      </div>
    </header>

    <main class="admin-main">
      {@render children?.()}
    </main>
  </div>
</div>

<AboutModal show={showAbout} onclose={() => showAbout = false} />

<style>
  .admin-layout {
    min-height: 100vh;
    display: flex;
    background: var(--bg-primary);
  }

  /* Sidebar */
  .sidebar {
    width: 220px;
    min-width: 220px;
    background: var(--color-accent);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    height: 100vh;
    position: sticky;
    top: 0;
    color: var(--color-gray);
  }

  .sidebar-header {
    padding: 20px 16px 16px;
    border-bottom: 1px solid var(--border);
    text-align: center;
  }

  .sidebar-logo {
    display: block;
    margin: 0 auto 8px;
    width: 64px;
    height: 64px;
    object-fit: contain;
  }

  .sidebar-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--color-primary);
    letter-spacing: 0.5px;
  }

  .sidebar-nav {
    flex: 1;
    padding: 12px 8px;
    display: flex;
    flex-direction: column;
    gap: 4px;
    overflow-y: auto;
  }

  .sidebar-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border: none;
    border-radius: 8px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
    text-align: left;
    width: 100%;
  }

  .sidebar-link:hover {
    background: var(--color-accent-hover);
    color: var(--color-gray);
  }

  .sidebar-link.active {
    background: var(--color-primary);
    color: #32373c;
    font-weight: 600;
  }

  .link-icon {
    font-size: 18px;
    width: 24px;
    text-align: center;
    flex-shrink: 0;
  }

  .link-label {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .sidebar-footer {
    padding: 16px;
    border-top: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .sidebar-user {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .sidebar-role {
    font-size: 11px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  /* Right content area */
  .admin-right {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .admin-header {
    display: flex;
    align-items: center;
    padding: 12px 24px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    position: relative;
    z-index: 1;
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

  .header-right {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 8px;
    position: relative;
    z-index: 1;
  }

  .header-right :global(.logout-btn) {
    position: static;
  }

  .admin-main {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
  }

  .sidebar-about {
    background: none;
    border: 1px solid var(--border);
    border-radius: 4px;
    font-size: 16px;
    color: var(--text-secondary);
    cursor: pointer;
    opacity: 0.8;
    transition: opacity 0.2s, color 0.2s;
    padding: 4px 10px;
    line-height: 1;
  }

  .sidebar-about:hover {
    opacity: 1;
    color: var(--color-primary);
  }

</style>