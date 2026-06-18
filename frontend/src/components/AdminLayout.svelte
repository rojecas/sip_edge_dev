<script>
  /**
   * AdminLayout — Layout for admin views.
   * Sidebar navigation (left) + header with LogoutButton + content slot.
   */
  import { authStore } from "../stores/auth.js";
  import { navigate, getRoute } from "../lib/router.js";
  import LogoutButton from "./LogoutButton.svelte";

  let { children } = $props();

  let currentRoute = $derived(getRoute());

  const links = [
    { route: "/admin", label: "Dashboard", icon: "📊" },
    { route: "/admin/config", label: "Configuración", icon: "⚙️" },
    { route: "/admin/usuarios", label: "Usuarios", icon: "👥" },
    { route: "/admin/haciendas", label: "Haciendas", icon: "🏠" },
    { route: "/admin/suertes", label: "Suertes", icon: "🌱" },
    { route: "/admin/backup", label: "Backup", icon: "💾" },
  ];

  function goTo(route) {
    navigate(route);
  }
</script>

<div class="admin-layout">
  <aside class="sidebar">
    <div class="sidebar-header">
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
      <span class="sidebar-user">{authStore.$authStore.username || "Admin"}</span>
      <span class="sidebar-role">admin</span>
    </div>
  </aside>

  <div class="admin-right">
    <header class="admin-header">
      <div class="header-left">
        <span class="user-info">
          {authStore.$authStore.username || "Admin"}
          <span class="role-badge">admin</span>
        </span>
      </div>
      <div class="header-right">
        <LogoutButton />
      </div>
    </header>

    <main class="admin-main">
      {@render children?.()}
    </main>
  </div>
</div>

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
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    height: 100vh;
    position: sticky;
    top: 0;
  }

  .sidebar-header {
    padding: 20px 16px 16px;
    border-bottom: 1px solid var(--border);
  }

  .sidebar-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--accent);
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
    background: var(--bg-input);
    color: var(--text-primary);
  }

  .sidebar-link.active {
    background: var(--accent);
    color: white;
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
  }

  .header-right :global(.logout-btn) {
    position: static;
  }

  .admin-main {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
  }
</style>
