<script>
  /**
   * KioskForm — Main weighing form for operators.
   * Includes: vehicle info, hacienda/suerte dropdowns, 3 weight fields,
   * live scale reader, confirm/reset buttons.
   */
  import { onMount } from "svelte";
  import { api, ApiError, buildQuery } from "../lib/api.js";
  import { ENDPOINTS, CONFIG } from "../lib/constants.js";
  import { authStore } from "../stores/auth.js";
  import { emergencyStore } from "../stores/emergency.js";
  import ScaleReader from "./ScaleReader.svelte";
  import WeightField from "./WeightField.svelte";
  import ConfirmModal from "./ConfirmModal.svelte";

  // Vehicle fields
  let tractomula = $state("");
  let vagon = $state("");
  let guia = $state("");

  // Hacienda / Suerte
  let haciendas = $state([]);
  let selectedHaciendaId = $state(null);
  let suertes = $state([]);
  let selectedSuerteId = $state(null);
  let haciendasLoading = $state(false);
  let suertesLoading = $state(false);
  let haciendasError = $state("");

  // Weight fields
  let pesoMuestra = $state(0);
  let pesoMineral = $state(0);
  let pesoVegetal = $state(0);

  // Emergency mode — makes weight fields editable
  let isEmergencyMode = $derived(emergencyStore.isEmergencyMode);

  // State
  let isSubmitting = $state(false);
  let successMessage = $state("");
  let errorMessage = $state("");
  let showResetConfirm = $state(false);

  // Load haciendas on mount
  onMount(() => {
    loadHaciendas();
  });

  async function loadHaciendas() {
    haciendasLoading = true;
    haciendasError = "";
    try {
      const params = {
        page: 1,
        page_size: CONFIG.DEFAULT_HACIENDAS_PAGE_SIZE,
        sort_by: "nombre",
        sort_order: "asc",
      };
      const data = await api.get(`${ENDPOINTS.HACIENDAS}${buildQuery(params)}`);
      haciendas = data.items || [];

      // If there are more pages, load them in background
      if (data.total_pages > 1) {
        loadRemainingHaciendas(data.total_pages);
      }
    } catch (err) {
      haciendasError = err instanceof ApiError ? err.message : "Error al cargar haciendas";
    } finally {
      haciendasLoading = false;
    }
  }

  async function loadRemainingHaciendas(totalPages) {
    for (let p = 2; p <= totalPages; p++) {
      try {
        const params = {
          page: p,
          page_size: CONFIG.DEFAULT_HACIENDAS_PAGE_SIZE,
        };
        const data = await api.get(`${ENDPOINTS.HACIENDAS}${buildQuery(params)}`);
        haciendas = [...haciendas, ...(data.items || [])];
      } catch {
        // Silently fail for background loading
      }
    }
  }

  async function onHaciendaChange() {
    suertes = [];
    selectedSuerteId = null;

    if (!selectedHaciendaId) return;

    suertesLoading = true;
    try {
      const data = await api.get(
        `${ENDPOINTS.SUERTES}?hacienda_id=${selectedHaciendaId}`
      );
      suertes = Array.isArray(data) ? data : (data.items || data);
    } catch {
      suertes = [];
    } finally {
      suertesLoading = false;
    }
  }

  function resetForm() {
    tractomula = "";
    vagon = "";
    guia = "";
    selectedHaciendaId = null;
    selectedSuerteId = null;
    suertes = [];
    pesoMuestra = 0;
    pesoMineral = 0;
    pesoVegetal = 0;
    successMessage = "";
    errorMessage = "";
  }

  async function handleReset() {
    showResetConfirm = true;
  }

  function confirmReset() {
    showResetConfirm = false;
    try {
      api.post(ENDPOINTS.WEIGHINGS_RESET);
    } catch {
      // ignore errors from reset endpoint
    }
    resetForm();
  }

  function cancelReset() {
    showResetConfirm = false;
  }

  function isFormValid() {
    return (
      tractomula.trim() !== "" &&
      vagon.trim() !== "" &&
      guia.trim() !== "" &&
      selectedHaciendaId !== null &&
      selectedHaciendaId !== undefined &&
      selectedSuerteId !== null &&
      selectedSuerteId !== undefined
    );
  }

  async function handleConfirm() {
    if (!isFormValid() || isSubmitting) return;

    isSubmitting = true;
    errorMessage = "";
    successMessage = "";

    try {
      const body = {
        tractomula: tractomula.trim(),
        vagon: vagon.trim(),
        numero_guia: guia.trim(),
        hacienda_id: selectedHaciendaId,
        suerte_id: selectedSuerteId,
        peso_muestra: pesoMuestra || 0,
        peso_mineral: pesoMineral || 0,
        peso_vegetal_extrano: pesoVegetal || 0,
        manual_entry: isEmergencyMode,
      };
      await api.post(ENDPOINTS.WEIGHINGS, body);
      successMessage = "Pesaje registrado exitosamente";
      // Clear form after 1.5 seconds
      setTimeout(() => {
        resetForm();
      }, 1500);
    } catch (err) {
      if (err instanceof ApiError) {
        errorMessage = err.message;
      } else {
        errorMessage = "Error al registrar el pesaje";
      }
    } finally {
      isSubmitting = false;
    }
  }
</script>

<div class="kiosk-form">
  <ScaleReader />

  <div class="form-grid">
    <!-- Columna izquierda: datos del vehículo -->
    <div class="form-section">
      <h3>Vehículo</h3>

      <div class="field">
        <label for="tractomula">Tractomula</label>
        <input
          id="tractomula"
          type="text"
          bind:value={tractomula}
          placeholder="Placa tractomula"
          class="text-input"
        />
      </div>

      <div class="field">
        <label for="vagon">Vagón</label>
        <input
          id="vagon"
          type="text"
          bind:value={vagon}
          placeholder="Identificador vagón"
          class="text-input"
        />
      </div>

      <div class="field">
        <label for="guia">Guía</label>
        <input
          id="guia"
          type="text"
          bind:value={guia}
          placeholder="Número de guía"
          class="text-input"
        />
      </div>
    </div>

    <!-- Columna derecha: hacienda/suerte -->
    <div class="form-section">
      <h3>Procedencia</h3>

      <div class="field">
        <label for="hacienda">Hacienda</label>
        {#if haciendasLoading}
          <p class="loading-text">Cargando haciendas...</p>
        {:else if haciendasError}
          <p class="error-text">{haciendasError}</p>
        {:else}
          <select
            id="hacienda"
            bind:value={selectedHaciendaId}
            onchange={onHaciendaChange}
            class="select-input"
          >
            <option value={null}>Seleccione una hacienda</option>
            {#each haciendas as h}
              <option value={h.id}>{h.codigo} — {h.nombre}</option>
            {/each}
          </select>
        {/if}
      </div>

      <div class="field">
        <label for="suerte">Suerte</label>
        {#if !selectedHaciendaId}
          <p class="hint-text">Seleccione una hacienda primero</p>
        {:else if suertesLoading}
          <p class="loading-text">Cargando suertes...</p>
        {:else if suertes.length === 0}
          <p class="hint-text">Sin suertes disponibles</p>
        {:else}
          <select
            id="suerte"
            bind:value={selectedSuerteId}
            class="select-input"
          >
            <option value={null}>Seleccione una suerte</option>
            {#each suertes as s}
              <option value={s.id}>{s.codigo_suerte}</option>
            {/each}
          </select>
        {/if}
      </div>
    </div>
  </div>

  <!-- Pesos -->
  <div class="form-section">
    <h3>Pesos</h3>
    <div class="weights-grid">
      <WeightField fieldName="Peso Muestra" bind:value={pesoMuestra} disabled={!isEmergencyMode} />
      <WeightField fieldName="Peso Mineral" bind:value={pesoMineral} disabled={!isEmergencyMode} />
      <WeightField fieldName="Peso Vegetal" bind:value={pesoVegetal} disabled={!isEmergencyMode} />
    </div>
  </div>

  <!-- Messages -->
  {#if successMessage}
    <div class="message success">{successMessage}</div>
  {/if}
  {#if errorMessage}
    <div class="message error">{errorMessage}</div>
  {/if}

  <!-- Action buttons -->
  <div class="form-actions">
    <button
      type="button"
      class="btn-reset"
      onclick={handleReset}
      disabled={isSubmitting}
    >
      Reset
    </button>
    <button
      type="button"
      class="btn-confirm"
      onclick={handleConfirm}
      disabled={!isFormValid() || isSubmitting}
    >
      {isSubmitting ? "Registrando..." : "Confirmar Pesaje"}
    </button>
  </div>
</div>

{#if showResetConfirm}
  <ConfirmModal
    show={showResetConfirm}
    title="Limpiar Formulario"
    message="¿Está seguro de limpiar el formulario?"
    confirmText="Limpiar"
    cancelText="Cancelar"
    onConfirm={confirmReset}
    onCancel={cancelReset}
  />
{/if}

<style>
  .kiosk-form {
    max-width: 960px;
    margin: 0 auto;
  }

  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 24px;
  }

  .form-section {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }

  .form-section h3 {
    font-size: 16px;
    color: var(--text-secondary);
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }

  .field {
    margin-bottom: 14px;
  }

  .field:last-child {
    margin-bottom: 0;
  }

  .field label {
    display: block;
    font-size: 14px;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 6px;
  }

  .text-input, .select-input {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 16px;
    outline: none;
    transition: border-color 0.2s;
  }

  .text-input:focus, .select-input:focus {
    border-color: var(--accent);
  }

  .select-input {
    cursor: pointer;
    appearance: auto;
  }

  .loading-text, .hint-text {
    font-size: 14px;
    color: var(--text-secondary);
    margin: 0;
    padding: 10px 0;
  }

  .error-text {
    font-size: 14px;
    color: var(--error);
    margin: 0;
  }

  .weights-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
  }

  .message {
    padding: 12px 16px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 16px;
  }

  .message.success {
    background: rgba(81, 207, 102, 0.1);
    color: var(--success);
  }

  .message.error {
    background: rgba(255, 107, 107, 0.1);
    color: var(--error);
  }

  .form-actions {
    display: flex;
    gap: 16px;
    justify-content: flex-end;
    margin-top: 8px;
  }

  .btn-reset {
    padding: 14px 32px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 16px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-reset:hover:not(:disabled) {
    background: var(--bg-input);
  }

  .btn-confirm {
    padding: 14px 40px;
    border: none;
    border-radius: 8px;
    background: var(--success);
    color: white;
    font-size: 18px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-confirm:hover:not(:disabled) {
    background: #3da84a;
  }

  .btn-confirm:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
