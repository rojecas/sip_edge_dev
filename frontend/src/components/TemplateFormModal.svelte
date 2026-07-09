<script>
  /**
   * TemplateFormModal — Modal for creating/editing report templates.
   * Props: show, mode ("create"|"edit"), plantilla, error, onClose, onSave.
   * onSave receives the payload object.
   *
   * Fase 8: Reemplaza recipients_text por selector multiple de usuarios
   * con checkboxes. Envia user_ids en vez de recipients.
   */
  import { onMount } from "svelte";
  import { api, ApiError } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";

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
    selectedUserIds: [],
    metrics: [],
    is_active: true,
  });

  let validationError = $state("");
  let submitting = $state(false);

  // User selector state
  let allUsers = $state([]);
  let availableUsers = $state([]);
  let usersLoading = $state(false);
  let usersError = $state("");
  let userSearch = $state("");

  $effect(() => {
    if (show) {
      validationError = "";
      submitting = false;
      userSearch = "";
      if (mode === "edit" && plantilla) {
        form = {
          name: plantilla.name || "",
          schedule: Array.isArray(plantilla.schedule) ? [...plantilla.schedule] : [],
          selectedUserIds: Array.isArray(plantilla.recipient_ids)
            ? [...plantilla.recipient_ids] : [],
          metrics: Array.isArray(plantilla.metrics) ? [...plantilla.metrics] : [],
          is_active: plantilla.is_active !== undefined ? plantilla.is_active : true,
        };
      } else {
        form = {
          name: "",
          schedule: [],
          selectedUserIds: [],
          metrics: [],
          is_active: true,
        };
      }
      loadUsers();
    }
  });

  async function loadUsers() {
    usersLoading = true;
    usersError = "";
    try {
      const result = await api.get(ENDPOINTS.USERS + "?page_size=100");
      const users = Array.isArray(result) ? result : (result.items || []);
      allUsers = users;
      // Filter: only admin + corresponsal, active
      availableUsers = users.filter(
        u => (u.role === "admin" || u.role === "corresponsal") && u.is_active
      );
    } catch (err) {
      usersError = err instanceof ApiError ? err.message : "Error al cargar usuarios.";
      availableUsers = [];
    } finally {
      usersLoading = false;
    }
  }

  let filteredUsers = $derived(
    userSearch.trim()
      ? availableUsers.filter(u =>
          u.full_name.toLowerCase().includes(userSearch.toLowerCase())
        )
      : availableUsers
  );

  function toggleUser(userId) {
    if (form.selectedUserIds.includes(userId)) {
      form.selectedUserIds = form.selectedUserIds.filter(id => id !== userId);
    } else {
      form.selectedUserIds = [...form.selectedUserIds, userId];
    }
  }

  function selectAll() {
    form.selectedUserIds = filteredUsers.map(u => u.id);
  }

  function deselectAll() {
    form.selectedUserIds = [];
  }

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

    const payload = {
      name: form.name.trim(),
      schedule: form.schedule,
      user_ids: form.selectedUserIds,
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

        <!-- Destinatarios: user selector with checkboxes -->
        <fieldset class="field-group">
          <legend>
            Destinatarios
            {#if form.selectedUserIds.length > 0}
              <span class="selected-count">({form.selectedUserIds.length} seleccionados)</span>
            {/if}
          </legend>

          {#if usersLoading}
            <span class="loading-text">Cargando usuarios...</span>
          {:else if usersError}
            <span class="error-text">{usersError}</span>
          {:else if availableUsers.length === 0}
            <span class="hint-text">No hay usuarios admin o corresponsal activos.</span>
          {:else}
            <div class="user-selector-controls">
              <input
                type="text"
                bind:value={userSearch}
                placeholder="Buscar por nombre..."
                class="search-input"
              />
              <div class="selector-actions">
                <button type="button" class="btn-link" onclick={selectAll}>Seleccionar todos</button>
                <button type="button" class="btn-link" onclick={deselectAll}>Deseleccionar</button>
              </div>
            </div>
            <div class="user-checkbox-list">
              {#each filteredUsers as user (user.id)}
                <label class="checkbox-label user-row">
                  <input
                    type="checkbox"
                    checked={form.selectedUserIds.includes(user.id)}
                    onchange={() => toggleUser(user.id)}
                  />
                  <span class="user-name">{user.full_name}</span>
                  <span class="user-phone">{user.phone || "Sin teléfono"}</span>
                </label>
              {:else}
                <span class="hint-text">Sin resultados para "{userSearch}".</span>
              {/each}
            </div>
          {/if}
        </fieldset>

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

  /* User selector styles */
  .selected-count {
    font-weight: 400;
    font-size: 12px;
    color: var(--accent);
  }

  .loading-text {
    color: var(--text-secondary);
    font-size: 12px;
    font-style: italic;
  }

  .error-text {
    color: var(--error);
    font-size: 12px;
  }

  .hint-text {
    color: var(--text-secondary);
    font-size: 12px;
    font-style: italic;
  }

  .user-selector-controls {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 8px;
  }

  .search-input {
    padding: 8px 10px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg-input);
    color: var(--text-primary);
    font-size: 13px;
  }

  .search-input:focus {
    outline: none;
    border-color: var(--accent);
  }

  .selector-actions {
    display: flex;
    gap: 12px;
  }

  .btn-link {
    background: none;
    border: none;
    color: var(--accent);
    font-size: 12px;
    cursor: pointer;
    padding: 0;
    text-decoration: underline;
  }

  .btn-link:hover {
    color: var(--accent-hover);
  }

  .user-checkbox-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-top: 4px;
    max-height: 180px;
    overflow-y: auto;
  }

  .user-row {
    padding: 4px 6px;
    border-radius: 4px;
    transition: background 0.15s;
  }

  .user-row:hover {
    background: var(--bg-input);
  }

  .user-name {
    flex: 1;
    font-size: 13px;
    color: var(--text-primary);
  }

  .user-phone {
    font-size: 12px;
    color: var(--text-secondary);
  }
</style>
