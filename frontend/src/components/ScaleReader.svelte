<script>
  /**
   * ScaleReader — Live weight indicator from WebSocket.
   * Shows weight and connection status via border color.
   */
  import { onMount, onDestroy } from "svelte";
  import { scaleStore, connect, disconnect } from "../lib/ws.js";
  import { authStore } from "../stores/auth.js";

  let { pesoMuestra = 0, pesoMineral = 0, pesoVegetal = 0 } = $props();

  let netoCana = $derived(Number(pesoMuestra) - Number(pesoMineral) - Number(pesoVegetal));

  onMount(() => {
    if (authStore.token) {
      connect(authStore.token);
    }
  });

  onDestroy(() => {
    disconnect();
  });

</script>

<div class="scale-reader" class:disconnected={!$scaleStore.connected}>
  <div class="weight-display">
    <span class="weight-value">{formatWeight($scaleStore.net_weight)}</span>
    <span class="weight-unit">{$scaleStore.unit}</span>
  </div>
</div>

<style>
  .scale-reader {
    background: var(--bg-secondary);
    border: 2px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    margin-bottom: 24px;
  }

  .scale-reader.disconnected {
    border-color: var(--error);
    opacity: 0.7;
  }

  .weight-display {
    display: flex;
    align-items: baseline;
    justify-content: center;
    gap: 8px;
  }

  .weight-label {
    font-size: 16px;
    color: var(--accent);
    font-weight: 600;
    margin-right: 8px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .weight-value {
    font-size: 40px;
    font-weight: 700;
    color: var(--text-primary);
    font-family: "Courier New", monospace;
    line-height: 1;
  }

  .weight-unit {
    font-size: 20px;
    color: var(--text-secondary);
    font-weight: 400;
  }
</style>