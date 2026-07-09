/** SIP-Edge Frontend Constants — API URLs, endpoints, and configuration. */

export const API_BASE = "";

export const ENDPOINTS = {
  LOGIN: "/api/auth/login",
  VERIFY_RESET_PIN: "/api/auth/verify-reset-pin",
  COMPLETE_RESET: "/api/auth/complete-reset",
  WEIGHINGS: "/api/weighings",
  WEIGHINGS_RESET: "/api/weighings/reset",
  HACIENDAS: "/api/haciendas",
  HACIENDAS_BY_ID: "/api/haciendas/",
  SUERTES: "/api/suertes",
  SUERTES_BY_ID: "/api/suertes/",
  EMERGENCY_STATUS: "/api/emergency/status",
  EMERGENCY_ADMINS: "/api/emergency/admins",
  EMERGENCY_REQUEST: "/api/emergency/request",
  // Admin panel endpoints
  CONFIG: "/api/config",
  CONFIG_TEST: "/api/config/test",
  SETUP_SESSION: "/api/setup/session",
  SETUP_SCALE: "/api/setup/scale",
  USERS: "/api/users",
  USERS_BY_ID: "/api/users/",
  BACKUP_STATUS: "/api/backup/status",
  BACKUP_RUN: "/api/backup/run",
  WS_SCALE: "/ws/scale",
  // Analytics endpoints
  REPORTS_TEMPLATES: "/api/reports/templates",
  REPORTS_TEMPLATES_BY_ID: "/api/reports/templates/",
  ANOMALIES_HISTORY: "/api/anomalies/history",
  ANOMALIES_DETECT: "/api/anomalies",
  AGENT_QUERY: "/api/agent/query",
  SCALE_COMMAND: "/api/scale/command",
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

export const HARVEST_TYPES = [
  "Manual - Incendio",
  "Manual - Quemado",
  "Manual - Verde",
  "Mecanico - Incendio",
  "Mecanico - Verde",
  "No convencional - Verde",
];
