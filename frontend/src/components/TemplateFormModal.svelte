<script>
  /**
   * TemplateFormModal — Modal for creating/editing report templates.
   * Props: show, mode ("create"|"edit"), plantilla, error, onClose, onSave.
   * onSave receives the payload object.
   */
  import { onMount } from "svelte";

  let {
    show = false,
    mode = "create",
    plantilla = null,
    error = "",
    onClose = () => {},
    onSave = () => {},
  } = $props();

  const METRICS = [
    { value: "count", label: "Cantidad de pesajes" },
    { value: "avg", label: "Promedio de pesos" },
    { value: "min_max", label: "Mínimo y máximo" },
    { value: "breakdown_by_hacienda", label: "Desglose por hacienda" },
    { value: "breakdown_by_operator", label: "Desglose por operador" },
    { value: "composition", label: "Composición de materia" },
    { value: "anomaly_count", label: "Cantidad de anomalías" },
    { value: "trend", label: "Tendencia" },
  ];

  const SCHEDULE_HOURS = [
    "00:00", "01:00", "02:00", "03:00", "04:00", "05:00",
    "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
    "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
    "18:00", "19:00", "20:00", "21:00", "22:00", "23:00",
  ];

  let form = $state({
    name: "",
    schedule: [],
    recipients_text: "",
    metrics: [],
    is_active: true,
  });

  let validationError = $state("");
  let submitting = $state(false);

  $effect(() => {
    if (show) {
      validationError = "";
      submitting = false;
      if (mode === "edit" && plantilla) {
        form = {
          name: plantilla.name || "",
          schedule: Array.isArray(plantilla.schedule) ? [...plantilla.schedule] : [],
          recipients_text: Array.isArray(plantilla.recipients)
            ? plantilla.recipients.join(", ") : "",
          metrics: Array.isArray(plantilla.metrics) ? [...plantilla.metrics] : [],
          is_active: plantilla.is_active !== undefined ? plantilla.is_active : true,
        };
      } else {
        form = {
          name: "",
          schedule: [],
          recipients_text: "",
          metrics: [],
          is_active: true,
        };
      }
    }
  });

  function toggleMetric(value) {
    if (form.metrics.includes(value)) {
      form.metrics = form.metrics.filter(m => m !== value);
    } else {
      form.metrics = [...form.metrics, value];
    }
  }

  function toggleScheduleHour(hour) {
    if (form.schedule.includes(hour)) {
      form.schedule = form.schedule.filter(h => h !== hour);
    } else {
      form.schedule = [...form.schedule, hour];
    }
  }

  function validate() {
    if (!form.name.trim()) return "El nombre de la plantilla es requerido.";
    return "";
  }

  async function handleSubmit() {
    const vErr = validate();
    if (vErr) {
      validationError = vErr;
      return;
    }
    validationError = "";
    submitting = true;

    const recipients = form.recipients_text
      .split(",")
      .map(s => s.trim())
      .filter(s => s.length > 0);

    const payload = {
      name: form.name.trim(),
      schedule: form.schedule,
      recipients: recipients,
      metrics: form.metrics,
      is_active: form.is_active,
    };

    await onSave(payload);
    submitting = false;
  }

  function handleOverlayClick(e) {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }
</script>

{#if show}
  <div class="modal-overlay" onclick={handleOverlayClick}>
    <div class="modal-container">
      <div class="modal-header">
        <h3>{mode === "create" ? "Nueva Plantilla" : "Editar Plantilla"}</h3>
        <button class="btn-close" onclick={onClose} aria-label="Cerrar">&times;</button>
      </div>

      {#if validationError || error}
        <div class="modal-error">{validationError || error}</div>
      {/if}

      <div class="modal-body">
        <label>
          Nombre
          <input type="text" bind:value={form.name} placeholder="Nombre de la plantilla" />
        </label>

        <!-- Schedule: multi-select hours -->
        <fieldset class="field-group">
          <legend>Horarios de envío</legend>
          <div class="checkbox-grid">
            {#each SCHEDULE_HOURS as hour}
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.schedule.includes(hour)}
                  onchange={() => toggleScheduleHour(hour)}
                />
                {hour}
              </label>
            {/each}
          </div>
        </fieldset>

        <!-- Metrics: checkboxes -->
        <fieldset class="field-group">
          <legend>Métricas</legend>
          <div class="checkbox-list">
            {#each METRICS as metric}
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  checked={form.metrics.includes(metric.value)}
                  onchange={() => toggleMetric(metric.value)}
                />
                {metric.label}
              </label>
            {/each}
          </div>
        </fieldset>

        <label>
          Destinatarios SMS
          <input
            type="text"
            bind:value={form.recipients_text}
            placeholder="Teléfonos separados por coma (ej. 573001234567, 573007654321)"
          />
        </label>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={form.is_active} />
          Activo
        </label>
      </div>

      <div class="modal-actions">
        <button class="btn-cancel" onclick={onClose} disabled={submitting}>Cancelar</button>
        <button class="btn-confirm" onclick={handleSubmit} disabled={submitting}>
          {submitting ? "Guardando..." : "Guardar"}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.75);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2000;
  }

  .modal-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 28px;
    width: 100%;
    max-width: 560px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .modal-header h3 {
    margin: 0;
    font-size: 18px;
    color: var(--text-primary);
  }

  .btn-close {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 22px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
  }

  .modal-error {
    background: rgba(255, 107, 107, 0.1);
    color: var(--error);
    border: 1px solid var(--error);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 16px;
    font-size: 13px;
  }

  .modal-body {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 24px;
  }

  .modal-body label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 13px;
    color: var(--text-secondary);
  }

  .checkbox-label {
    flex-direction: row !important;
    align-items: center;
    gap: 8px;
  }

  .checkbox-label input[type="checkbox"] {
    width: 16px;
    height: 16px;
    accent-color: var(--accent);
  }

  .field-group {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 14px;
  }

  .field-group legend {
    font-size: 13px;
    color: var(--text-secondary);
    font-weight: 500;
    padding: 0 4px;
  }

  .checkbox-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 4px 8px;
    margin-top: 8px;
  }

  .checkbox-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    margin-top: 8px;
  }

  .modal-body input[type="text"],
  .modal-body select {
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 14px;
  }

  .modal-body input:focus,
  .modal-body select:focus {
    outline: none;
    border-color: var(--accent);
  }

  .modal-actions {
    display: flex;
    gap: 12px;
    justify-content: flex-end;
  }

  .btn-cancel {
    padding: 10px 20px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: transparent;
    color: var(--text-secondary);
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-cancel:hover:not(:disabled) { background: var(--bg-input); }

  .btn-confirm {
    padding: 10px 20px;
    border: none;
    border-radius: 8px;
    background: var(--accent);
    color: white;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  .btn-confirm:hover:not(:disabled) { background: var(--accent-hover); }

  .btn-confirm:disabled,
  .btn-cancel:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
