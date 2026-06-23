/**
 * API fetch wrapper — automatic JWT, 401 interception, JSON parsing.
 */

const API_BASE = "";

let _authStore = null;

/**
 * Set the auth store reference. Called once during app initialization.
 * @param {object} store - authStore instance
 */
export function setAuthStore(store) {
  _authStore = store;
}

/**
 * Build headers with authorization if token exists.
 */
function buildHeaders() {
  const headers = {
    "Content-Type": "application/json",
  };
  if (_authStore && _authStore.token) {
    headers["Authorization"] = `Bearer ${_authStore.token}`;
  }
  return headers;
}

/**
 * Core request function with 401 interception.
 * @param {string} url - full URL path (e.g. "/api/weighings")
 * @param {object} [options] - fetch options
 * @returns {Promise<any>} parsed JSON response
 */
async function request(url, options = {}) {
  const opts = {
    ...options,
    headers: {
      ...buildHeaders(),
      ...(options.headers || {}),
    },
  };

  // Remove Content-Type for GET/DELETE without body
  if (!opts.body) {
    delete opts.headers["Content-Type"];
  }

  let response;
  try {
    response = await fetch(`${API_BASE}${url}`, opts);
  } catch (err) {
    throw new ApiError("Error de conexión. Verifique que el servidor esté disponible.", 0, err);
  }

  // Intercept 401 — force logout
  if (response.status === 401) {
    if (_authStore) {
      _authStore.logout();
    }
    throw new ApiError("Sesión expirada o no autorizada.", 401, null);
  }

  // For 204 No Content or empty responses
  if (response.status === 204) {
    return null;
  }

  let data;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail = Array.isArray(data?.detail)
        ? data.detail.map(d => d.msg).join(". ")
        : (data?.detail || `Error del servidor (${response.status})`);
    throw new ApiError(detail, response.status, data);
  }

  return data;
}

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

/**
 * Public API methods.
 */
export const api = {
  get(url) {
    return request(url, { method: "GET" });
  },

  post(url, body) {
    return request(url, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  put(url, body) {
    return request(url, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    });
  },

  del(url) {
    return request(url, { method: "DELETE" });
  },
};

/**
 * Helper to build query string from params object.
 * @param {object} params
 * @returns {string}
 */
export function buildQuery(params = {}) {
  const parts = [];
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
    }
  }
  return parts.length ? `?${parts.join("&")}` : "";
}
