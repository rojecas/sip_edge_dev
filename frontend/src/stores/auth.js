/**
 * Auth store — reactive authentication state using svelte/store.
 * Shared across all components. Backward-compatible with existing authStore API.
 */
import { writable, derived, get } from "svelte/store";
import { API_BASE, ENDPOINTS, LS_KEYS, ROLES } from "../lib/constants.js";

function decodeJwtPayload(token) {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = parts[1];
    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(decoded);
  } catch {
    return null;
  }
}

function getSessionTimeout(payload) {
  if (payload && payload.session_timeout_minutes) return payload.session_timeout_minutes;
  return 30;
}

function readLS(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}

function writeLS(key, value) {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch { /* ignore */ }
}

// Internal writable stores
const _token = writable(readLS(LS_KEYS.TOKEN));
const _role = writable(readLS(LS_KEYS.ROLE));
const _username = writable(readLS(LS_KEYS.USERNAME));
const _lastActivity = writable(Date.now() / 1000);

// Derived stores
const _isAuthenticated = derived([_token, _role], ([$t, $r]) => !!$t && !!$r);
const _isOperator = derived([_role], ([$r]) => $r === ROLES.OPERATOR);
const _isAdmin = derived([_role], ([$r]) => $r === ROLES.ADMIN);
const _jwtPayload = derived([_token], ([$t]) => $t ? decodeJwtPayload($t) : null);

// Combined readable store for $authStore auto-subscription
function createAuthStore() {
  const { subscribe } = derived(
    [_token, _role, _username, _isAuthenticated, _isOperator, _isAdmin, _jwtPayload, _lastActivity],
    ([$t, $r, $u, $ia, $io, $iad, $jp, $la]) => ({
      token: $t, role: $r, username: $u,
      isAuthenticated: $ia, isOperator: $io, isAdmin: $iad,
      jwtPayload: $jp, lastActivity: $la
    })
  );
  return {
    subscribe,
    get token() { return get(_token); },
    set token(v) { _token.set(v); },
    get role() { return get(_role); },
    set role(v) { _role.set(v); },
    get username() { return get(_username); },
    set username(v) { _username.set(v); },
    get isAuthenticated() { return get(_isAuthenticated); },
    get isOperator() { return get(_isOperator); },
    get isAdmin() { return get(_isAdmin); },
    get jwtPayload() { return get(_jwtPayload); },
    get lastActivity() { return get(_lastActivity); },
    login(newToken, newRole, newUsername) {
      _token.set(newToken);
      _role.set(newRole);
      _username.set(newUsername || "");
      _lastActivity.set(Date.now() / 1000);
      writeLS(LS_KEYS.TOKEN, newToken);
      writeLS(LS_KEYS.ROLE, newRole);
      if (newUsername) writeLS(LS_KEYS.USERNAME, newUsername);
    },
    logout() {
      _token.set(null);
      _role.set(null);
      _username.set(null);
      writeLS(LS_KEYS.TOKEN, null);
      writeLS(LS_KEYS.ROLE, null);
      writeLS(LS_KEYS.USERNAME, null);
    },
    updateLastActivity() {
      _lastActivity.set(Date.now() / 1000);
    },
    async refreshToken() {
      const currentToken = get(_token);
      if (!currentToken) return;
      try {
        const response = await fetch(`${API_BASE}${ENDPOINTS.REFRESH}`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${currentToken}`,
            "Content-Type": "application/json",
          },
        });
        if (!response.ok) {
          // If refresh fails (e.g. 401), logout
          this.logout();
          return;
        }
        const data = await response.json();
        this.login(data.access_token, data.role, get(_username));
      } catch {
        // Network error — do nothing, try again next interval
      }
    },
    decodeJwtPayload,
    getSessionTimeout,
  };
}

export const authStore = createAuthStore();
