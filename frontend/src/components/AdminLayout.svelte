<script>
  /**
   * AdminLayout — Layout for admin views.
   * Header with LogoutButton, slot for admin content.
   */
  import { authStore } from "../stores/auth.js";
  import LogoutButton from "./LogoutButton.svelte";

  let { children } = $props();
</script>

<div class="admin-layout">
  <header class="admin-header">
    <div class="header-left">
      <span class="user-info">
        {authStore.username || "Admin"}
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

<style>
  .admin-layout {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary);
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
