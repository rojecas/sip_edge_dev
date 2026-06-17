/**
 * WebSocket manager for /ws/scale.
 * Reactive store: { net_weight, is_stable, unit, connected }
 * Auto-reconnect up to 5 attempts with 2s interval.
 */

import { CONFIG, ENDPOINTS } from "./constants.js";

/** Build WebSocket URL from current window location. */
function buildWsUrl(token) {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  return `${protocol}//${host}${ENDPOINTS.WS_SCALE}?token=${encodeURIComponent(token)}`;
}

// Reactive state
let net_weight = $state(0.0);
let is_stable = $state(false);
let unit = $state("kg");
let connected = $state(false);

let _ws = null;
let _reconnectAttempts = 0;
let _reconnectTimer = null;
let _shouldReconnect = true;

/**
 * Connect to WebSocket /ws/scale.
 * @param {string} token - JWT token
 */
export function connect(token) {
  if (!token) return;

  _shouldReconnect = true;
  _reconnectAttempts = 0;
  _doConnect(token);
}

function _doConnect(token) {
  if (_ws) {
    try {
      _ws.close();
    } catch {
      // ignore
    }
    _ws = null;
  }

  try {
    _ws = new WebSocket(buildWsUrl(token));
  } catch {
    _handleDisconnect(token);
    return;
  }

  _ws.onopen = () => {
    connected = true;
    _reconnectAttempts = 0;
  };

  _ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "scale_reading" && msg.data) {
        net_weight = msg.data.net_weight ?? net_weight;
        is_stable = msg.data.is_stable ?? is_stable;
        unit = msg.data.unit ?? unit;
      }
    } catch {
      // ignore malformed messages
    }
  };

  _ws.onclose = () => {
    connected = false;
    _handleDisconnect(token);
  };

  _ws.onerror = () => {
    // onclose will be called after onerror
  };
}

function _handleDisconnect(token) {
  if (!_shouldReconnect) return;

  _reconnectAttempts++;
  if (_reconnectAttempts <= CONFIG.WS_RECONNECT_ATTEMPTS) {
    _reconnectTimer = setTimeout(() => {
      _doConnect(token);
    }, CONFIG.WS_RECONNECT_INTERVAL_MS);
  } else {
    connected = false;
    net_weight = 0.0;
    is_stable = false;
  }
}

/**
 * Disconnect WebSocket and stop reconnection.
 */
export function disconnect() {
  _shouldReconnect = false;
  if (_reconnectTimer) {
    clearTimeout(_reconnectTimer);
    _reconnectTimer = null;
  }
  if (_ws) {
    try {
      _ws.close();
    } catch {
      // ignore
    }
    _ws = null;
  }
  connected = false;
  net_weight = 0.0;
  is_stable = false;
}

/**
 * Reactive scale store. Access via ws.scaleStore in components.
 * In Svelte 5, use $derived or import these directly.
 */
export const scaleStore = {
  get net_weight() { return net_weight; },
  set net_weight(v) { net_weight = v; },
  get is_stable() { return is_stable; },
  set is_stable(v) { is_stable = v; },
  get unit() { return unit; },
  get connected() { return connected; },
};
