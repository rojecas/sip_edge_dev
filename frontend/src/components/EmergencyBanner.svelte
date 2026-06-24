<script>
  import { onMount, onDestroy } from "svelte";
  import { api } from "../lib/api.js";
  import { ENDPOINTS, CONFIG } from "../lib/constants.js";
  import { emergencyStore } from "../stores/emergency.js";

  let manualMode = $state(false);
  let timeRemaining = $state("");
  let timer = null;

  async function checkStatus() {
    try {
      const data = await api.get(ENDPOINTS.EMERGENCY_STATUS);
      manualMode = data.active === true;
      emergencyStore.isEmergencyMode = manualMode;
      if (data.remaining_seconds !== undefined) {
        const hours = data.remaining_seconds / 3600;
        timeRemaining = formatTime(hours);
      }
    } catch {}
  }

  function formatTime(hours) {
    if (hours === null || hours === undefined) return "";
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    if (h === 0 && m === 0) return "< 1 min";
    let parts = [];
    if (h > 0) parts.push(`${h}h`);
    if (m > 0) parts.push(`${m}m`);
    return parts.join(" ");
  }

  onMount(() => {
    checkStatus();
    timer = setInterval(checkStatus, CONFIG.POLLING_INTERVAL_MS);
  });
  onDestroy(() => { if (timer) clearInterval(timer); });
</script>

{#if manualMode}
  <div class="emergency-banner">
    <span class="banner-text">
      MODO MANUAL ACTIVO — Pesos editables
      {#if timeRemaining}
        <span class="time-remaining">({timeRemaining} restante)</span>
      {/if}
    </span>
  </div>
{/if}

<style>
  .emergency-banner {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 24px;
    background: linear-gradient(90deg, #b33a00, #cc4400);
    color: white; font-size: 15px; font-weight: 600; gap: 16px; flex-wrap: wrap;
  }
  .banner-text { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .time-remaining { font-weight: 400; opacity: 0.85; font-size: 13px; }
</style>
