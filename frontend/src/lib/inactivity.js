/**
 * Inactivity checker — compares JWT iat with current time.
 * If session expired, calls authStore.logout().
 */

import { CONFIG } from "./constants.js";

/**
 * Check if the JWT session has expired based on iat and session timeout.
 * @param {object|null} jwtPayload - decoded JWT payload
 * @param {number} sessionTimeoutMinutes - configured session timeout in minutes
 * @returns {boolean} true if session is expired
 */
export function checkInactivity(jwtPayload, sessionTimeoutMinutes) {
  if (!jwtPayload || !jwtPayload.iat) {
    return true; // no valid iat — treat as expired
  }

  const now = Date.now() / 1000; // seconds
  const elapsed = now - jwtPayload.iat;
  const timeout = (sessionTimeoutMinutes || CONFIG.DEFAULT_SESSION_TIMEOUT_MINUTES) * 60;

  return elapsed > timeout;
}

/**
 * Start inactivity monitoring timer.
 * Calls onExpired callback when session expires.
 * @param {function} getPayload - returns current JWT payload (or null)
 * @param {function} getTimeout - returns session timeout in minutes
 * @param {function} onExpired - called when session expires
 * @returns {function} stop function to clear the timer
 */
export function startInactivityTimer(getPayload, getTimeout, onExpired) {
  const interval = setInterval(() => {
    const payload = getPayload();
    const timeout = getTimeout();
    if (checkInactivity(payload, timeout)) {
      clearInterval(interval);
      onExpired();
    }
  }, CONFIG.INACTIVITY_CHECK_INTERVAL_MS);

  return () => clearInterval(interval);
}
