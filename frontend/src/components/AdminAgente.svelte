<script>
  /**
   * AdminAgente — AI agent chat console.
   * Sends queries via POST /api/agent/query, shows conversation history.
   */
  import { onMount } from "svelte";
  import { api, ApiError } from "../lib/api.js";
  import { ENDPOINTS } from "../lib/constants.js";

  let messages = $state([]);
  let inputText = $state("");
  let loading = $state(false);
  let sendError = $state("");
  let failedMessageIndex = $state(-1);

  let chatContainer = $state(null);

  onMount(() => {
    messages = [
      {
        role: "system",
        content: "Bienvenido a la consola del Agente IA. Puede realizar consultas en lenguaje natural sobre los datos de pesajes, anomalías y reportes.",
      },
    ];
    scrollToBottom();
  });

  function scrollToBottom() {
    // Use setTimeout to allow DOM update first
    setTimeout(() => {
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 50);
  }

  async function handleSend() {
    const text = inputText.trim();
    if (!text) return;

    // Add user message
    messages = [...messages, { role: "user", content: text }];
    inputText = "";
    sendError = "";
    failedMessageIndex = -1;
    loading = true;
    scrollToBottom();

    try {
      const result = await api.post(ENDPOINTS.AGENT_QUERY, { query: text });
      messages = [...messages, { role: "agent", content: result.response }];
    } catch (err) {
      const errMsg = err instanceof ApiError ? err.message : "Error de conexión.";
      messages = [...messages, { role: "error", content: errMsg }];
      failedMessageIndex = messages.length - 1;
      sendError = errMsg;
    } finally {
      loading = false;
      scrollToBottom();
    }
  }

  function handleRetry() {
    // Remove the last error message and retry sending the previous user message
    if (failedMessageIndex >= 0) {
      const failedMsg = messages[failedMessageIndex];
      messages = messages.filter((_, i) => i !== failedMessageIndex);
      const lastUser = [...messages].reverse().find(m => m.role === "user");
      if (lastUser) {
        inputText = lastUser.content;
        // Remove that user message too so it gets re-added in handleSend
        messages = messages.filter((_, i) => messages.indexOf(lastUser) !== i);
        handleSend();
      }
    }
  }

  function handleKeydown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }
</script>

<div class="agente-page">
  <div class="page-header">
    <h1>Agente IA</h1>
    <span class="page-subtitle">Consola de consultas al agente inteligente</span>
  </div>

  <div class="chat-area">
    <div class="chat-container" bind:this={chatContainer}>
      {#each messages as msg, i}
        {#if msg.role === "system"}
          <div class="msg-system">
            <span class="msg-icon">🤖</span>
            <div class="msg-content">{msg.content}</div>
          </div>
        {:else if msg.role === "user"}
          <div class="msg-user">
            <div class="msg-content">{msg.content}</div>
          </div>
        {:else if msg.role === "agent"}
          <div class="msg-agent">
            <span class="msg-icon">🤖</span>
            <div class="msg-content"><pre>{msg.content}</pre></div>
          </div>
        {:else if msg.role === "error"}
          <div class="msg-error">
            <div class="msg-content">
              <span class="error-icon">⚠️</span>
              {msg.content}
              {#if i === failedMessageIndex}
                <button class="btn-retry" onclick={handleRetry}>Reintentar</button>
              {/if}
            </div>
          </div>
        {/if}
      {/each}

      {#if loading}
        <div class="msg-agent msg-loading">
          <span class="msg-icon">🤖</span>
          <div class="msg-content">
            <span class="spinner"></span> Pensando...
          </div>
        </div>
      {/if}
    </div>

    <div class="chat-input">
      <textarea
        bind:value={inputText}
        placeholder="Escriba su consulta aquí..."
        disabled={loading}
        rows="2"
        onkeydown={handleKeydown}
      ></textarea>
      <button class="btn-send" onclick={handleSend} disabled={loading || !inputText.trim()}>
        {loading ? "..." : "Enviar"}
      </button>
    </div>
  </div>
</div>

<style>
  .agente-page { max-width: 900px; height: calc(100vh - 140px); display: flex; flex-direction: column; }
  .page-header { margin-bottom: 16px; flex-shrink: 0; }
  .page-header h1 { font-size: 24px; margin: 0 0 4px; }
  .page-subtitle { font-size: 14px; color: var(--text-secondary); }

  .chat-area {
    flex: 1; display: flex; flex-direction: column;
    border: 1px solid var(--border); border-radius: 12px;
    background: var(--bg-secondary); overflow: hidden;
    min-height: 0;
  }

  .chat-container {
    flex: 1; overflow-y: auto; padding: 20px;
    display: flex; flex-direction: column; gap: 12px;
  }

  .msg-system {
    display: flex; align-items: flex-start; gap: 8px;
    padding: 10px 14px; background: var(--bg-input);
    border-radius: 10px; font-size: 13px; color: var(--text-secondary);
  }

  .msg-system .msg-icon { font-size: 18px; flex-shrink: 0; }

  .msg-user {
    display: flex; justify-content: flex-end;
  }

  .msg-user .msg-content {
    max-width: 80%; background: var(--accent); color: white;
    padding: 10px 16px; border-radius: 14px 14px 4px 14px;
    font-size: 14px; word-wrap: break-word;
  }

  .msg-agent {
    display: flex; align-items: flex-start; gap: 8px;
  }

  .msg-agent .msg-icon { font-size: 18px; flex-shrink: 0; margin-top: 8px; }

  .msg-agent .msg-content {
    max-width: 85%; background: var(--bg-input);
    padding: 12px 16px; border-radius: 4px 14px 14px 14px;
    font-size: 14px; color: var(--text-primary); word-wrap: break-word;
  }

  .msg-agent .msg-content pre {
    margin: 0; white-space: pre-wrap; font-family: inherit;
  }

  .msg-loading .msg-content {
    display: flex; align-items: center; gap: 8px;
    color: var(--text-secondary);
  }

  .msg-error .msg-content {
    max-width: 80%; background: rgba(255, 107, 107, 0.1);
    border: 1px solid var(--error); color: var(--error);
    padding: 10px 16px; border-radius: 14px;
    font-size: 13px; display: flex; align-items: center; gap: 8px;
    flex-wrap: wrap;
  }

  .spinner {
    display: inline-block; width: 14px; height: 14px;
    border: 2px solid var(--border); border-top-color: var(--accent);
    border-radius: 50%; animation: spin 0.8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }

  .chat-input {
    display: flex; gap: 10px; padding: 16px;
    border-top: 1px solid var(--border); flex-shrink: 0;
  }

  .chat-input textarea {
    flex: 1; padding: 10px 14px; border: 1px solid var(--border);
    border-radius: 10px; background: var(--bg-input);
    color: var(--text-primary); font-size: 14px;
    resize: none; font-family: inherit;
  }

  .chat-input textarea:focus {
    outline: none; border-color: var(--accent);
  }

  .chat-input textarea:disabled { opacity: 0.5; }

  .btn-send {
    padding: 10px 20px; border: none; border-radius: 10px;
    background: var(--accent); color: white;
    font-size: 14px; font-weight: 600; cursor: pointer;
    transition: background 0.2s; white-space: nowrap;
    align-self: flex-end;
  }

  .btn-send:hover:not(:disabled) { background: var(--accent-hover); }
  .btn-send:disabled { opacity: 0.6; cursor: not-allowed; }

  .btn-retry {
    background: none; border: none; color: var(--accent);
    font-size: 13px; cursor: pointer; text-decoration: underline; padding: 0;
  }
</style>
