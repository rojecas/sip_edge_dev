/**
 * Auth store — reactive authentication state.
 * Uses Svelte 5 $state for reactivity. Shared across all components.
 */
import { LS_KEYS, ROLES } from "../lib/constants.js";

/** Decode JWT payload (without verification). Returns null if invalid. */
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

/** Extract session timeout from JWT or use default. */
function getSessionTimeout(payload) {
  if (payload && payload.session_timeout_minutes) {
    return payload.session_timeout_minutes;
  }
  return 30; // default
}

/** Read from localStorage with fallback. */
function readLS(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

/** Write to localStorage. */
function writeLS(key, value) {
  try {
    if (value === null) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, value);
    }
  } catch {
    // localStorage unavailable (private browsing, etc.)
  }
}

/**
 * Reactive auth state shared across the SPA.
 * Access via `authStore.token`, `authStore.role`, etc.
 */
let token = $state(readLS(LS_KEYS.TOKEN));
let role = $state(readLS(LS_KEYS.ROLE));
let username = $state(readLS(LS_KEYS.USERNAME));

/** Derived: is the user authenticated? */
let isAuthenticated = $derived(!!token && !!role);

/** Derived: is the user an operator? */
let isOperator = $derived(role === ROLES.OPERATOR);

/** Derived: is the user an admin? */
let isAdmin = $derived(role === ROLES.ADMIN);

/** Derived: decoded JWT payload */
let jwtPayload = $derived(token ? decodeJwtPayload(token) : null);

/**
 * Login — store token, role, username.
 * @param {string} newToken - JWT access token
 * @param {string} newRole - user role (admin|operator)
 * @param {string} [newUsername] - username
 */
function login(newToken, newRole, newUsername) {
  token = newToken;
  role = newRole;
  username = newUsername || "";
  writeLS(LS_KEYS.TOKEN, newToken);
  writeLS(LS_KEYS.ROLE, newRole);
  if (newUsername) writeLS(LS_KEYS.USERNAME, newUsername);
}

/**
 * Logout — clear all auth state.
 */
function logout() {
  token = null;
  role = null;
  username = null;
  writeLS(LS_KEYS.TOKEN, null);
  writeLS(LS_KEYS.ROLE, null);
  writeLS(LS_KEYS.USERNAME, null);
}

export const authStore = {
  get token() { return token; },
  set token(v) { token = v; },
  get role() { return role; },
  set role(v) { role = v; },
  get username() { return username; },
  set username(v) { username = v; },
  get isAuthenticated() { return isAuthenticated; },
  get isOperator() { return isOperator; },
  get isAdmin() { return isAdmin; },
  get jwtPayload() { return jwtPayload; },
  login,
  logout,
  decodeJwtPayload,
  getSessionTimeout,
};
