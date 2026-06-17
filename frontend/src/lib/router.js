/**
 * Simple SPA router using hash-based routing.
 * Returns reactive currentRoute for use in App.svelte.
 */

let currentRoute = $state(window.location.hash.slice(1) || "/");
let _listeners = [];

function notifyListeners() {
  for (const fn of _listeners) {
    try { fn(currentRoute); } catch { /* ignore */ }
  }
}

function setRoute(route) {
  currentRoute = route;
  window.location.hash = "#" + route;
  notifyListeners();
}

// Listen for hash changes (back/forward buttons)
window.addEventListener("hashchange", () => {
  currentRoute = window.location.hash.slice(1) || "/";
  notifyListeners();
});

/**
 * Navigate to a route.
 * @param {string} route - route path (e.g. "/kiosco")
 */
export function navigate(route) {
  setRoute(route);
}

/**
 * Replace current route (no history entry).
 * @param {string} route
 */
export function replaceRoute(route) {
  currentRoute = route;
  window.location.replace("#" + route);
  notifyListeners();
}

/**
 * Get current route reactively.
 */
export function getRoute() {
  return currentRoute;
}

/**
 * Register a route change listener.
 * @param {function} fn - callback receiving new route
 */
export function onRouteChange(fn) {
  _listeners.push(fn);
  return () => {
    _listeners = _listeners.filter((l) => l !== fn);
  };
}

/**
 * Check if a route matches the current route.
 * @param {string} pattern - route pattern (exact match)
 * @returns {boolean}
 */
export function isRoute(pattern) {
  return currentRoute === pattern;
}

// Export reactive store for use in components
export const router = {
  get route() { return currentRoute; },
  navigate,
  replaceRoute,
  isRoute,
  onRouteChange,
};
