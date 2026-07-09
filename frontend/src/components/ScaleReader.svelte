<script>
  /**
   * ScaleReader — Live weight indicator from WebSocket.
   * Shows weight and connection status via border color.
   */
  import { onMount, onDestroy } from "svelte";
  import { scaleStore, connect, disconnect } from "../lib/ws.js";
  import { authStore } from "../stores/auth.js";

  onMount(() => {
    if (authStore.token) {
      connect(authStore.token);
    }
  });

  onDestroy(() => {
    disconnect();
  });

  function formatWeight(val) {
    if (val === null || val === undefined) return "0.000";
    return Number(val).toFixed(3);
  }
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