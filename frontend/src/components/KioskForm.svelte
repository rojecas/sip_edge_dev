<script>
  /**
   * KioskForm — Main weighing form for operators.
   * Includes: vehicle info, hacienda/suerte dropdowns, 3 weight fields,
   * live scale reader, confirm/reset buttons.
   */
  import { onMount, onDestroy } from "svelte";
  import { get } from "svelte/store";
  import { api, ApiError } from "../lib/api.js";
  import { ENDPOINTS, HARVEST_TYPES } from "../lib/constants.js";
  import { authStore } from "../stores/auth.js";
  import { emergencyStore } from "../stores/emergency.js";
  import { onScaleReading } from "../lib/ws.js";
  import ScaleReader from "./ScaleReader.svelte";
  import WeightField from "./WeightField.svelte";
  import ConfirmModal from "./ConfirmModal.svelte";
  import HaciendaCodeInput from "./HaciendaCodeInput.svelte";
  import EmergencyModal from "./EmergencyModal.svelte";
  import NotesField from "./NotesField.svelte";

  // Vehicle fields
  let tractomula = $state("");
  let vagon = $state("");
  let guia = $state("");

  // Hacienda / Suerte
  let selectedHaciendaId = $state(null);
  let suertes = $state([]);
  let selectedSuerteId = $state(null);
  let suertesLoading = $state(false);

  let resetCounter = $state(0);
  // Weight fields
  let pesoMuestra = $state(0);
  let pesoMineral = $state(0);
  let pesoVegetal = $state(0);

  // Harvest type
  let tipoCosecha = $state("Mecanico - Verde");

  // Notas / observaciones
  let notas = $state("");

  // State
  let isSubmitting = $state(false);
  let successMessage = $state("");
  let errorMessage = $state("");
  let showResetConfirm = $state(false);
  let showEmergencyModal = $state(false);

  // Auto-capture PRINT notification
  let printNotification = $state("");
  let printNotificationTimer = null;

  /**
   * Auto-capture PRINT: when a scale_reading arrives via WebSocket,
   * assign the weight to the focused field or show a notification.
   */
  function handleScaleReading(data) {
    const activeEl = document.activeElement;
    // Check if a weight-input has focus
    if (activeEl && activeEl.classList.contains("weight-input")) {
      // Determine which field is focused by traversing to parent
      const fieldEl = activeEl.closest(".weight-field");
      if (fieldEl) {
        const label = fieldEl.querySelector(".field-label");
        if (label) {
          const labelText = label.textContent.trim();
          if (labelText.includes("Muestra")) {
            pesoMuestra = data.net_weight;
          } else if (labelText.includes("Mineral")) {
            pesoMineral = data.net_weight;
          } else if (labelText.includes("Vegetal")) {
            pesoVegetal = data.net_weight;
          }
        }
      }
    } else {
      // No weight field has focus — show temporary notification
      const weightStr = data.net_weight != null ? data.net_weight.toFixed(3) : "0.000";
      printNotification = `Peso recibido: ${weightStr} ${data.unit || "kg"}`;
      if (printNotificationTimer) clearTimeout(printNotificationTimer);
      printNotificationTimer = setTimeout(() => {
        printNotification = "";
      }, 3000);
    }
  }

  // Subscribe to scale readings for auto-capture PRINT
  onMount(() => {
    onScaleReading(handleScaleReading);
  });

  onDestroy(() => {
    if (printNotificationTimer) clearTimeout(printNotificationTimer);
  });

  /**
   * Handle hacienda selection from HaciendaCodeInput (R1).
   * Called with hacienda object on confirm, or null on clear.
   */
  function handleHaciendaSelect(hacienda) {
    if (hacienda) {
      selectedHaciendaId = hacienda.id;
      onHaciendaChange();
    } else {
      selectedHaciendaId = null;
      suertes = [];
      selectedSuerteId = null;
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
    tipoCosecha = "Mecanico - Verde";
    notas = "";
    successMessage = "";
    errorMessage = "";
    resetCounter++;
  }

  async function handleReset() {
    showResetConfirm = true;
  }

  async function confirmReset() {
    showResetConfirm = false;
    try {
      await api.post(ENDPOINTS.WEIGHINGS_RESET);
    } catch {
      // ignore errors from reset endpoint
    }
    resetForm();
  }

  function openEmergencyModal() { showEmergencyModal = true; }
  function closeEmergencyModal() { showEmergencyModal = false; }

  function cancelReset() {
    showResetConfirm = false;
  }

  async function handleResetPesoMuestra() {
    try {
      await api.post(ENDPOINTS.WEIGHINGS_RESET, { step: "peso_muestra" });
    } catch {
      // ignore errors from reset endpoint
    }
    pesoMuestra = 0;
  }

  async function handleResetPesoMineral() {
    try {
      await api.post(ENDPOINTS.WEIGHINGS_RESET, { step: "peso_mineral" });
    } catch {
      // ignore errors from reset endpoint
    }
    pesoMineral = 0;
  }

  async function handleResetPesoVegetal() {
    try {
      await api.post(ENDPOINTS.WEIGHINGS_RESET, { step: "peso_vegetal_extrano" });
    } catch {
      // ignore errors from reset endpoint
    }
    pesoVegetal = 0;
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
        manual_entry: get(emergencyStore),
        tipo_cosecha: tipoCosecha,
        notas: notas || null,
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
  <ScaleReader pesoMuestra={pesoMuestra} pesoMineral={pesoMineral} pesoVegetal={pesoVegetal} />

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
        <HaciendaCodeInput onSelect={handleHaciendaSelect} placeholder="Ingrese código de hacienda" resetKey={resetCounter} />
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

  <!-- Tipo de Cosecha -->
  <div class="form-section">
    <h3>Tipo de Cosecha</h3>
    <div class="field">
      <select
        id="tipo-cosecha"
        bind:value={tipoCosecha}
        class="select-input"
      >
        {#each HARVEST_TYPES as tipo}
          <option value={tipo}>{tipo}</option>
        {/each}
      </select>
    </div>
  </div>

  <!-- Pesos -->
  <div class="form-section">
    <h3>Pesos (kg)</h3>
    <div class="weights-grid">
      <WeightField fieldName="Peso Muestra" bind:value={pesoMuestra} disabled={!$emergencyStore} onReset={handleResetPesoMuestra} />
      <WeightField fieldName="Peso Vegetal" bind:value={pesoVegetal} disabled={!$emergencyStore} onReset={handleResetPesoVegetal} />
      <WeightField fieldName="Peso Mineral" bind:value={pesoMineral} disabled={!$emergencyStore} onReset={handleResetPesoMineral} />
    </div>
  </div>

  <!-- Notas colapsables -->
  <div class="form-section">
    <NotesField bind:notas={notas} />
  </div>

  <!-- Messages -->
  {#if printNotification}
    <div class="message notification">{printNotification}</div>
  {/if}
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
      class="btn-confirm"
      onclick={handleConfirm}
      disabled={!isFormValid() || isSubmitting}
    >
      {isSubmitting ? "Registrando..." : "Confirmar Medidas"}
    </button>
  </div>
</div>

  {#if showEmergencyModal}
    <EmergencyModal onclose={closeEmergencyModal} />
  {/if}

  <div class="emergency-section">
    <button class="btn-emergency" onclick={openEmergencyModal}>
      Solicitar Modo Manual
    </button>
    <button
      type="button"
      class="btn-clear-all"
      onclick={handleReset}
      disabled={isSubmitting}
    >
      Limpiar todo
    </button>
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
    max-width: 1280px;
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

  .message.notification {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    text-align: center;
    animation: fadeIn 0.3s ease;
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
    justify-content: center;
    margin-top: 8px;
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

  .emergency-section {
    display: flex;
    justify-content: center;
    gap: 16px;
    padding: 12px 0;
    margin-top: 8px;
    border-top: 1px solid var(--border);
  }

  .btn-emergency {
    padding: 8px 20px;
    border: none;
    border-radius: 6px;
    background: #e67e22;
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-emergency:hover {
    background: #d35400;
  }

  .btn-clear-all {
    padding: 8px 20px;
    border: none;
    border-radius: 6px;
    background: #e74c3c;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-clear-all:hover:not(:disabled) {
    background: #c0392b;
  }

  .btn-clear-all:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
  }
</style>
