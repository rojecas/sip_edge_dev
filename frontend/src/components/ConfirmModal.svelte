<script>
  /**
   * ConfirmModal — Generic reusable confirmation modal.
   * Props: title, message, confirmText, cancelText, onConfirm, onCancel.
   */
  let {
    show = false,
    title = "Confirmar",
    message = "¿Está seguro?",
    confirmText = "Confirmar",
    cancelText = "Cancelar",
    onConfirm = () => {},
    onCancel = () => {},
  } = $props();

  function handleOverlayClick(e) {
    if (e.target === e.currentTarget) {
      onCancel();
    }
  }
</script>

{#if show}
  <div class="modal-overlay" onclick={handleOverlayClick}>
    <div class="modal-container">
      <div class="modal-header">
        <h3>{title}</h3>
        <button class="btn-close" onclick={onCancel} aria-label="Cerrar">&times;</button>
      </div>
      <p class="modal-message">{message}</p>
      <div class="modal-actions">
        <button class="btn-cancel" onclick={onCancel}>{cancelText}</button>
        <button class="btn-confirm" onclick={onConfirm}>{confirmText}</button>
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
    max-width: 400px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
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

  .modal-message {
    margin: 0 0 24px;
    font-size: 15px;
    color: var(--text-secondary);
    line-height: 1.5;
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

  .btn-cancel:hover {
    background: var(--bg-input);
  }

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

  .btn-confirm:hover {
    background: var(--accent-hover);
  }
</style>
