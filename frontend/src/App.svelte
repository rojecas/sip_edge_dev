<script>
  /**
   * App.svelte — Root component.
   * Handles authentication state, routing, and layout selection.
   */
  import "./app.css";
  import { authStore } from "./stores/auth.js";
  import { setAuthStore, api } from "./lib/api.js";
  import { isRoute } from "./lib/router.js";
  import AuthModal from "./components/AuthModal.svelte";
  import InactivityGuard from "./components/InactivityGuard.svelte";
  import KioskLayout from "./components/KioskLayout.svelte";
  import AdminLayout from "./components/AdminLayout.svelte";
  import KioskForm from "./components/KioskForm.svelte";
  import HistoryTable from "./components/HistoryTable.svelte";
  import AdminPlaceholder from "./components/AdminPlaceholder.svelte";

  // Initialize auth store for the API wrapper
  setAuthStore(authStore);

  // Reactively track the current route
  let currentRoute = $state(window.location.hash.slice(1) || "/");

  // Listen for hash changes
  function onHashChange() {
    currentRoute = window.location.hash.slice(1) || "/";
  }

  $effect(() => {
    window.addEventListener("hashchange", onHashChange);
    onHashChange(); // initial read
    return () => window.removeEventListener("hashchange", onHashChange);
  });
</script>

{#if !authStore.isAuthenticated}
  <AuthModal />
{:else}
  <InactivityGuard />

  {#if authStore.isOperator}
    <KioskLayout>
      {#if currentRoute === "/kiosco/historial"}
        <HistoryTable />
      {:else}
        <KioskForm />
      {/if}
    </KioskLayout>
  {:else if authStore.isAdmin}
    <AdminLayout>
      <AdminPlaceholder />
    </AdminLayout>
  {/if}
{/if}
