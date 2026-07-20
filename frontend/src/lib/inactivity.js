/**
 * Inactivity checker — compares last user activity with session timeout.
 * If session expired, calls the onExpired callback.
 */

import { CONFIG } from "./constants.js";

/**
 * Check if the session has expired based on last activity and timeout.
 * @param {number|null} lastActivity - timestamp (seconds) of last user activity
 * @param {number} sessionTimeoutMinutes - configured session timeout in minutes
 * @returns {boolean} true if session is expired
 */
export function checkInactivity(lastActivity, sessionTimeoutMinutes) {
  if (lastActivity === null || lastActivity === undefined) {
    return true; // no activity recorded — treat as expired
  }

  const now = Date.now() / 1000; // seconds
  const elapsed = now - lastActivity;
  const timeout = (sessionTimeoutMinutes || CONFIG.DEFAULT_SESSION_TIMEOUT_MINUTES) * 60;

  return elapsed > timeout;
}

/**
 * Start inactivity monitoring timer.
 * Calls onExpired callback when session expires.
 * @param {function} getLastActivity - returns timestamp of last activity (or null)
 * @param {function} getTimeout - returns session timeout in minutes
 * @param {function} onExpired - called when session expires
 * @returns {function} stop function to clear the timer
 */
export function startInactivityTimer(getLastActivity, getTimeout, onExpired) {
  const interval = setInterval(() => {
    const last = getLastActivity();
    const timeout = getTimeout();
    if (checkInactivity(last, timeout)) {
      clearInterval(interval);
      onExpired();
    }
  }, CONFIG.INACTIVITY_CHECK_INTERVAL_MS);

  return () => clearInterval(interval);
}
