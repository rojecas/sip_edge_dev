<script>
  /**
   * AdminConfig — System configuration form for RS485, RS232, GSM, and timeouts.
   */
  import { onMount } from "svelte";
  import { api, ApiError } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";

  const BAUD_RATES = [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200];
  const PARITY_VALUES = ["N", "E", "O", "M", "S"];
  const DATA_BITS = [5, 6, 7, 8];
  const STOP_BITS = [1.0, 1.5, 2.0];

  // Form state
  let rs485 = $state({ path: "", baudrate: 9600, parity: "N", data_bits: 8, stop_bits: 1.0 });
  let rs232 = $state({ path: "", baudrate: 9600, parity: "N", data_bits: 8, stop_bits: 1.0 });
  let gsm = $state({ modem_index: 0 });
  let sessionTimeout = $state(15);
  let scaleTimeout = $state(3);

  // Load state
  let loading = $state(true);
  let loadError = $state("");

  // Global save state
  let saving = $state(false);
  let saveMsg = $state("");
  let saveError = $state("");

  // Test states
  let testing = $state({ rs485: false, rs232: false, gsm: false });
  let testResult = $state({ rs485: "", rs232: "", gsm: "" });
  let testError = $state({ rs485: "", rs232: "", gsm: "" });

  onMount(() => {
    loadConfig();
  });

  async function loadConfig() {
    loading = true;
    loadError = "";
    try {
      const data = await api.get(ENDPOINTS.CONFIG);
      if (data.rs485) { rs485 = { ...rs485, ...data.rs485 }; }
      if (data.rs232) { rs232 = { ...rs232, ...data.rs232 }; }
      if (data.gsm) { gsm = { ...gsm, ...data.gsm }; }
      if (data.session_timeout_minutes !== undefined) { sessionTimeout = data.session_timeout_minutes; }
      if (data.scale_timeout_seconds !== undefined || data.timeout_seconds !== undefined) {
        scaleTimeout = data.scale_timeout_seconds ?? data.timeout_seconds;
      }
    } catch (err) {
      loadError = err instanceof ApiError ? err.message : "Error de conexión al cargar configuración.";
    } finally {
      loading = false;
    }
  }

  async function saveConfig() {
    saving = true;
    saveMsg = "";
    saveError = "";
    try {
      // Save ports + GSM
      await api.put(ENDPOINTS.CONFIG, {
        rs485: { ...rs485 },
        rs232: { ...rs232 },
        gsm: { ...gsm },
      });
      // Save session timeout
      await api.put(ENDPOINTS.SETUP_SESSION, {
        session_timeout_minutes: sessionTimeout,
      });
      // Save scale timeout
      await api.put(ENDPOINTS.SETUP_SCALE, {
        timeout_seconds: scaleTimeout,
      });
      saveMsg = "Configuración guardada exitosamente.";
    } catch (err) {
      saveError = err instanceof ApiError ? err.message : "Error de conexión al guardar configuración.";
    } finally {
      saving = false;
    }
  }

  async function testPort(port) {
    testing = { ...testing, [port]: true };
    testResult = { ...testResult, [port]: "" };
    testError = { ...testError, [port]: "" };
    try {
      const data = await api.post(`${ENDPOINTS.CONFIG_TEST}/${port}`);
      if (data.status === "ok") {
        testResult = { ...testResult, [port]: "Prueba exitosa" };
      } else {
        testError = { ...testError, [port]: data.detail || "Prueba fallida" };
      }
    } catch (err) {
      testError = { ...testError, [port]: err instanceof ApiError ? err.message : "Error de conexión." };
    } finally {
      testing = { ...testing, [port]: false };
    }
  }
</script>

<div class="config-page">
  <h1>Configuración del Sistema</h1>

  {#if loading}
    <div class="loading">Cargando configuración...</div>
  {:else if loadError}
    <div class="error-box">{loadError}</div>
    <button class="btn btn-secondary" onclick={loadConfig}>Reintentar</button>
  {:else}
    <!-- RS485 Section -->
    <section class="config-section">
      <h2>Puerto RS485 (Báscula)</h2>
      <div class="form-grid">
        <label>Path <input type="text" bind:value={rs485.path} placeholder="/dev/ttyACM0" /></label>
        <label>Baudrate <select bind:value={rs485.baudrate}>{#each BAUD_RATES as b}<option value={b}>{b}</option>{/each}</select></label>
        <label>Paridad <select bind:value={rs485.parity}>{#each PARITY_VALUES as p}<option value={p}>{p}</option>{/each}</select></label>
        <label>Data Bits <select bind:value={rs485.data_bits}>{#each DATA_BITS as d}<option value={d}>{d}</option>{/each}</select></label>
        <label>Stop Bits <select bind:value={rs485.stop_bits}>{#each STOP_BITS as s}<option value={s}>{s}</option>{/each}</select></label>
      </div>
      <div class="test-row">
        {#if testResult.rs485}<span class="test-ok">{testResult.rs485}</span>{/if}
        {#if testError.rs485}<span class="test-fail">{testError.rs485}</span>{/if}
        <button class="btn btn-test-orange" disabled={testing.rs485} onclick={() => testPort("rs485")}>
          {testing.rs485 ? "Probando..." : "Test RS485"}
        </button>
      </div>
    </section>

    <!-- RS232 Section -->
    <section class="config-section">
      <h2>Puerto RS232 (PC Externo)</h2>
      <div class="form-grid">
        <label>Path <input type="text" bind:value={rs232.path} placeholder="/dev/ttyACM1" /></label>
        <label>Baudrate <select bind:value={rs232.baudrate}>{#each BAUD_RATES as b}<option value={b}>{b}</option>{/each}</select></label>
        <label>Paridad <select bind:value={rs232.parity}>{#each PARITY_VALUES as p}<option value={p}>{p}</option>{/each}</select></label>
        <label>Data Bits <select bind:value={rs232.data_bits}>{#each DATA_BITS as d}<option value={d}>{d}</option>{/each}</select></label>
        <label>Stop Bits <select bind:value={rs232.stop_bits}>{#each STOP_BITS as s}<option value={s}>{s}</option>{/each}</select></label>
      </div>
      <div class="test-row">
        {#if testResult.rs232}<span class="test-ok">{testResult.rs232}</span>{/if}
        {#if testError.rs232}<span class="test-fail">{testError.rs232}</span>{/if}
        <button class="btn btn-test-orange" disabled={testing.rs232} onclick={() => testPort("rs232")}>
          {testing.rs232 ? "Probando..." : "Test RS232"}
        </button>
      </div>
    </section>

    <!-- GSM Section -->
    <section class="config-section">
      <h2>Módem GSM</h2>
      <div class="form-grid-gsm">
        <label>Modem Index <input type="number" bind:value={gsm.modem_index} min="0" /></label>
      </div>
      <div class="test-row">
        {#if testResult.gsm}<span class="test-ok">{testResult.gsm}</span>{/if}
        {#if testError.gsm}<span class="test-fail">{testError.gsm}</span>{/if}
        <button class="btn btn-test-orange" disabled={testing.gsm} onclick={() => testPort("gsm")}>
          {testing.gsm ? "Probando..." : "Test GSM"}
        </button>
      </div>
    </section>

    <!-- Timeouts Section -->
    <section class="config-section">
      <h2>Timeouts</h2>
      <div class="timeout-row">
        <label>Session Timeout (minutos) <input type="number" bind:value={sessionTimeout} min="1" /></label>
        <label>Scale Timeout (segundos) <input type="number" bind:value={scaleTimeout} min="1" max="10" /></label>
      </div>
    </section>

    <!-- Single Save Button -->
    <div class="save-global">
      <button class="btn btn-primary" disabled={saving} onclick={saveConfig}>
        {saving ? "Guardando..." : "Guardar Configuración"}
      </button>
      {#if saveMsg}<span class="save-ok">{saveMsg}</span>{/if}
      {#if saveError}<span class="save-fail">{saveError}</span>{/if}
    </div>
  {/if}
</div>

<style>
  .config-page {
    max-width: 1100px;
  }

  h1 { font-size: 24px; margin-bottom: 24px; }
  h2 { font-size: 17px; margin: 0 0 16px; }
  .loading { color: var(--text-secondary); font-size: 15px; padding: 24px 0; }
  .error-box { color: var(--error); font-size: 14px; margin-bottom: 12px; }

  .config-section {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
  }

  .form-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 16px;
  }

  .form-grid-gsm {
    display: flex;
    max-width: 250px;
    margin-bottom: 16px;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 13px;
    color: var(--text-secondary);
  }

  input, select {
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 14px;
  }

  input:focus, select:focus { outline: none; border-color: var(--accent); }
  select { cursor: pointer; }

  .test-row {
    display: flex;
    align-items: center;
    gap: 12px;
    justify-content: flex-end;
    flex-wrap: wrap;
  }

  .test-ok { color: var(--success); font-size: 14px; font-weight: 500; }
  .test-fail { color: var(--error); font-size: 14px; font-weight: 500; }

  .save-global {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-top: 4px;
    flex-wrap: wrap;
  }

  .save-ok { color: var(--success); font-size: 13px; font-weight: 500; }
  .save-fail { color: var(--error); font-size: 13px; font-weight: 500; }

  .timeout-row {
    display: flex;
    gap: 32px;
    flex-wrap: wrap;
  }

  .timeout-row label { min-width: 220px; }

  .btn {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
    white-space: nowrap;
  }

  .btn:disabled { opacity: 0.6; cursor: not-allowed; }

  .btn-primary { background: var(--accent); color: white; }
  .btn-primary:hover:not(:disabled) { background: var(--accent-hover); }

  .btn-secondary { background: var(--bg-input); color: var(--text-primary); border: 1px solid var(--border); }
  .btn-secondary:hover:not(:disabled) { background: var(--border); }

  .btn-test-orange {
    background: #e67e22;
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
    white-space: nowrap;
  }

  .btn-test-orange:hover:not(:disabled) { background: #d35400; }
  .btn-test-orange:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
