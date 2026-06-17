/** SIP-Edge Frontend Constants — API URLs, endpoints, and configuration. */

export const API_BASE = "";

export const ENDPOINTS = {
  LOGIN: "/api/auth/login",
  VERIFY_RESET_PIN: "/api/auth/verify-reset-pin",
  COMPLETE_RESET: "/api/auth/complete-reset",
  WEIGHINGS: "/api/weighings",
  WEIGHINGS_RESET: "/api/weighings/reset",
  HACIENDAS: "/api/haciendas",
  SUERTES: "/api/suertes",
  EMERGENCY_STATUS: "/api/emergency/status",
  EMERGENCY_ADMINS: "/api/emergency/admins",
  EMERGENCY_REQUEST: "/api/emergency/request",
  WS_SCALE: "/ws/scale",
};

export const CONFIG = {
  DEFAULT_SESSION_TIMEOUT_MINUTES: 30,
  WS_RECONNECT_ATTEMPTS: 5,
  WS_RECONNECT_INTERVAL_MS: 2000,
  POLLING_INTERVAL_MS: 5000,
  INACTIVITY_CHECK_INTERVAL_MS: 60000,
  DEFAULT_PAGE_SIZE: 20,
  DEFAULT_HACIENDAS_PAGE_SIZE: 100,
  MAX_PAGE_SIZE: 100,
};

export const ROLES = {
  ADMIN: "admin",
  OPERATOR: "operator",
};

export const LS_KEYS = {
  TOKEN: "sip_edge_token",
  ROLE: "sip_edge_role",
  USERNAME: "sip_edge_username",
};
