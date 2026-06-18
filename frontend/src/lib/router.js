/**
 * Simple SPA router using hash-based routing.
 * Uses svelte/store for reactive state.
 */
import { writable, get } from "svelte/store";

const _currentRoute = writable(window.location.hash.slice(1) || "/");

let _listeners = [];

function notifyListeners() {
  const route = get(_currentRoute);
  for (const fn of _listeners) {
    try { fn(route); } catch { /* ignore */ }
  }
}

function setRoute(route) {
  _currentRoute.set(route);
  window.location.hash = "#" + route;
  notifyListeners();
}

// Listen for hash changes (back/forward buttons)
window.addEventListener("hashchange", () => {
  _currentRoute.set(window.location.hash.slice(1) || "/");
  notifyListeners();
});

export function navigate(route) {
  setRoute(route);
}

export function replaceRoute(route) {
  _currentRoute.set(route);
  window.location.replace("#" + route);
  notifyListeners();
}

export function getRoute() {
  return get(_currentRoute);
}

export function onRouteChange(fn) {
  _listeners.push(fn);
  return () => {
    _listeners = _listeners.filter((l) => l !== fn);
  };
}

export function isRoute(pattern) {
  return get(_currentRoute) === pattern;
}

export const router = {
  subscribe: _currentRoute.subscribe,
  get route() { return get(_currentRoute); },
  navigate,
  replaceRoute,
  isRoute,
  onRouteChange,
};
