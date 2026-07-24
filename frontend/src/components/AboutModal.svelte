<script>
  /**
   * AboutModal — Corporate info, copyright, version, and legal disclaimer.
   * Triggered by ⓘ icon in Login, Kiosko, and Admin views.
   */
  let { show = false, onclose = () => {} } = $props();
</script>

{#if show}
  <div class="about-overlay" onclick={onclose} role="dialog">
    <div class="about-card" onclick={(e) => e.stopPropagation()}>
      <button class="about-close" onclick={onclose}>&times;</button>
      <div class="about-logo">
        <img src="/favicon.png" alt="Mayaguez" width="48" height="48" />
      </div>
      <h2>Ingenio Mayagüez S.A.</h2>
      <p class="about-subtitle">SIP-Edge v1.0</p>
      <hr />
      <p class="about-copy">&copy; 2026 Ingenio Mayagüez S.A. Todos los derechos reservados.</p>
      <p class="about-disclaimer">
        Sistema de uso exclusivo. Prohibida su reproducción total o parcial
        sin autorización del Ingenio Mayagüez S.A.
      </p>
    </div>
  </div>
{/if}

<style>
  .about-overlay {
    position: fixed; inset: 0; z-index: 5000;
    background: rgba(0,0,0,0.6);
    display: flex; align-items: center; justify-content: center;
  }
  .about-card {
    background: var(--bg-secondary, #1e1e2e);
    border: 1px solid var(--border, #333);
    border-radius: 12px;
    padding: 32px 40px;
    max-width: 400px; width: 90%;
    text-align: center;
    position: relative;
    color: var(--text-primary, #e0e0e0);
  }
  .about-close {
    position: absolute; top: 8px; right: 12px;
    background: none; border: none; font-size: 24px;
    color: var(--text-secondary, #888); cursor: pointer;
  }
  .about-logo { margin-bottom: 12px; }
  .about-logo img { border-radius: 8px; }
  h2 { font-size: 18px; margin: 0 0 4px; font-weight: 700; }
  .about-subtitle { font-size: 13px; color: var(--text-secondary, #888); margin: 0 0 16px; }
  hr { border: none; border-top: 1px solid var(--border, #333); margin: 16px 0; }
  .about-copy { font-size: 13px; color: var(--text-secondary, #888); margin: 0 0 8px; }
  .about-disclaimer { font-size: 12px; color: var(--text-secondary, #888); line-height: 1.5; margin: 0; }
</style>