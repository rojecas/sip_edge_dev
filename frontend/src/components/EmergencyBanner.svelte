<script>
  import { onMount, onDestroy } from "svelte";
  import { api } from "../lib/api.js";
  import { ENDPOINTS, CONFIG } from "../lib/constants.js";
  import { emergencyStore } from "../stores/emergency.js";
  import EmergencyModal from "./EmergencyModal.svelte";

  let manualMode = $state(false);
  let timeRemaining = $state("");
  let showModal = $state(false);
  let timer = null;

  async function checkStatus() {
    try {
      const data = await api.get(ENDPOINTS.EMERGENCY_STATUS);
      manualMode = data.manual_mode === true;
      emergencyStore.isEmergencyMode = manualMode;
      if (data.remaining_hours !== undefined) {
        timeRemaining = formatTime(data.remaining_hours);
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

  function openModal() { showModal = true; }
  function closeModal() { showModal = false; }

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
    <button class="btn-request" onclick={openModal}>Solicitar Modo Manual</button>
  </div>
{/if}

{#if showModal}
  <EmergencyModal onclose={closeModal} />
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
  .btn-request {
    padding: 8px 18px;
    border: 2px solid rgba(255,255,255,0.5); border-radius: 6px;
    background: rgba(255,255,255,0.1); color: white; font-size: 13px;
    font-weight: 600; cursor: pointer; white-space: nowrap;
  }
  .btn-request:hover { background: rgba(255,255,255,0.2); border-color: white; }
</style>
