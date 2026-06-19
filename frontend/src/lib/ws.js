/**
 * WebSocket manager for /ws/scale.
 * Reactive store using svelte/store.
 */
import { writable, get, derived } from "svelte/store";
import { CONFIG, ENDPOINTS } from "./constants.js";

function buildWsUrl(token) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return protocol + "//" + host + ENDPOINTS.WS_SCALE + "?token=" + encodeURIComponent(token);
}

// Reactive state
const _net_weight = writable(0.0);
const _is_stable = writable(false);
const _unit = writable("kg");
const _connected = writable(false);

let _ws = null;
let _reconnectAttempts = 0;
let _reconnectTimer = null;
let _shouldReconnect = true;

export function connect(token) {
  if (!token) return;
  _shouldReconnect = true;
  _reconnectAttempts = 0;
  _doConnect(token);
}

function _doConnect(token) {
  if (_ws) {
    try { _ws.close(); } catch { /* ignore */ }
    _ws = null;
  }

  try {
    _ws = new WebSocket(buildWsUrl(token));
  } catch {
    _handleDisconnect(token);
    return;
  }

  _ws.onopen = () => {
    _connected.set(true);
    _reconnectAttempts = 0;
  };

  _ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "scale_reading" && msg.data) {
        if (msg.data.net_weight !== undefined) _net_weight.set(msg.data.net_weight);
        if (msg.data.is_stable !== undefined) _is_stable.set(msg.data.is_stable);
        if (msg.data.unit !== undefined) _unit.set(msg.data.unit);
      }
    } catch { /* ignore */ }
  };

  _ws.onclose = () => {
    _connected.set(false);
    _handleDisconnect(token);
  };

  _ws.onerror = () => { /* onclose will follow */ };
}

function _handleDisconnect(token) {
  if (!_shouldReconnect) return;
  _reconnectAttempts++;
  if (_reconnectAttempts <= CONFIG.WS_RECONNECT_ATTEMPTS) {
    _reconnectTimer = setTimeout(() => {
      _doConnect(token);
    }, CONFIG.WS_RECONNECT_INTERVAL_MS);
  } else {
    _connected.set(false);
    _net_weight.set(0.0);
    _is_stable.set(false);
  }
}

export function disconnect() {
  _shouldReconnect = false;
  if (_reconnectTimer) {
    clearTimeout(_reconnectTimer);
    _reconnectTimer = null;
  }
  if (_ws) {
    try { _ws.close(); } catch { /* ignore */ }
    _ws = null;
  }
  _connected.set(false);
  _net_weight.set(0.0);
  _is_stable.set(false);
}

export const scaleStore = derived(
  [_net_weight, _is_stable, _unit, _connected],
  ([$w, $s, $u, $c]) => ({
    net_weight: $w,
    is_stable: $s,
    unit: $u,
    connected: $c
  })
);
