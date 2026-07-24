<script>
  /**
   * App.svelte — Root component.
   * Handles authentication state, routing, and layout selection.
   */
  import "./app.css";
  import { authStore } from "./stores/auth.js";
  import { setAuthStore } from "./lib/api.js";
  import AuthModal from "./components/AuthModal.svelte";
  import InactivityGuard from "./components/InactivityGuard.svelte";
  import KioskLayout from "./components/KioskLayout.svelte";
  import AdminLayout from "./components/AdminLayout.svelte";
  import KioskForm from "./components/KioskForm.svelte";
  import HistoryTable from "./components/HistoryTable.svelte";
  import AdminDashboard from "./components/AdminDashboard.svelte";
  import AdminConfig from "./components/AdminConfig.svelte";
  import AdminUsers from "./components/AdminUsers.svelte";
  import AdminHaciendas from "./components/AdminHaciendas.svelte";
  import AdminSuertes from "./components/AdminSuertes.svelte";
  import AdminBackup from "./components/AdminBackup.svelte";
  import AdminReportes from "./components/AdminReportes.svelte";
  import AdminAnomalias from "./components/AdminAnomalias.svelte";
  import AdminAgente from "./components/AdminAgente.svelte";

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

{#if !$authStore.isAuthenticated}
  <AuthModal />
{:else}
  <InactivityGuard />

  {#if $authStore.isOperator || ($authStore.isAdmin && currentRoute.startsWith("/kiosko"))}
    <KioskLayout>
      {#if currentRoute === "/kiosco/historial"}
        <HistoryTable />
      {:else if currentRoute === "/kiosco/haciendas"}
        <div class="kiosk-admin-wrapper">
          <AdminHaciendas allowDelete={false} />
        </div>
      {:else if currentRoute === "/kiosco/suertes"}
        <div class="kiosk-admin-wrapper">
          <AdminSuertes allowDelete={false} />
        </div>
      {:else}
        <KioskForm />
      {/if}
    </KioskLayout>
  {:else if $authStore.isAdmin}
    <AdminLayout>
      {#if currentRoute === "/admin"}
        <AdminDashboard />
      {:else if currentRoute === "/admin/config"}
        <AdminConfig />
      {:else if currentRoute === "/admin/usuarios"}
        <AdminUsers />
      {:else if currentRoute === "/admin/haciendas"}
        <AdminHaciendas />
      {:else if currentRoute === "/admin/suertes"}
        <AdminSuertes />
      {:else if currentRoute === "/admin/backup"}
        <AdminBackup />
      {:else if currentRoute === "/admin/reportes"}
        <AdminReportes />
      {:else if currentRoute === "/admin/anomalias"}
        <AdminAnomalias />
      {:else if currentRoute === "/admin/agente"}
        <AdminAgente />
      {:else}
        <AdminDashboard />
      {/if}
    </AdminLayout>
  {/if}
{/if}

