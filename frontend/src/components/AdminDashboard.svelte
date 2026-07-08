<script>
  /**
   * AdminDashboard — Dashboard with quick-access cards for each admin section.
   */
  import { navigate } from "../lib/router.js";

  const cards = [
    {
      route: "/admin/config",
      icon: "⚙️",
      title: "Configuración",
      description: "Puertos RS485, RS232, GSM y timeouts del sistema.",
    },
    {
      route: "/admin/usuarios",
      icon: "👥",
      title: "Usuarios",
      description: "Crear, editar y desactivar usuarios del sistema.",
    },
    {
      route: "/admin/haciendas",
      icon: "🏠",
      title: "Haciendas",
      description: "Gestionar haciendas con eliminación lógica.",
    },
    {
      route: "/admin/suertes",
      icon: "🌱",
      title: "Suertes",
      description: "Gestionar suertes filtradas por hacienda.",
    },
    {
      route: "/admin/reportes",
      icon: "📋",
      title: "Reportes",
      description: "Plantillas de reportes programados.",
    },
    {
      route: "/admin/anomalias",
      icon: "⚠️",
      title: "Anomalías",
      description: "Historial de anomalías detectadas.",
    },
    {
      route: "/admin/agente",
      icon: "🤖",
      title: "Agente IA",
      description: "Consola de consultas al agente inteligente.",
    },
    {
      route: "/admin/backup",
      icon: "💾",
      title: "Backup",
      description: "Historial y ejecución de respaldos del sistema.",
    },
  ];

  function goTo(route) {
    navigate(route);
  }
</script>

<div class="dashboard">
  <h1 class="dashboard-title">Panel de Administración</h1>
  <p class="dashboard-subtitle">Seleccione una sección para comenzar</p>

  <div class="cards-grid">
    {#each cards as card}
      <button class="card" onclick={() => goTo(card.route)}>
        <span class="card-icon">{card.icon}</span>
        <h3 class="card-title">{card.title}</h3>
        <p class="card-desc">{card.description}</p>
      </button>
    {/each}
  </div>
</div>

<style>
  .dashboard {
    padding: 8px 0;
  }

  .dashboard-title {
    font-size: 26px;
    margin-bottom: 4px;
  }

  .dashboard-subtitle {
    font-size: 15px;
    color: var(--text-secondary);
    margin: 0 0 32px;
  }

  .cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 20px;
  }

  .card {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    padding: 28px 24px;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: var(--bg-secondary);
    cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
    text-align: left;
    width: 100%;
    color: inherit;
  }

  .card:hover {
    border-color: var(--accent);
    box-shadow: 0 4px 16px rgba(233, 69, 96, 0.15);
    transform: translateY(-2px);
  }

  .card-icon {
    font-size: 36px;
    margin-bottom: 14px;
  }

  .card-title {
    font-size: 17px;
    font-weight: 600;
    margin: 0 0 8px;
    color: var(--text-primary);
  }

  .card-desc {
    font-size: 13px;
    color: var(--text-secondary);
    margin: 0;
    line-height: 1.5;
  }
</style>
