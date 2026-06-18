/**
 * Emergency mode store — shared reactive state using svelte/store.
 */
import { writable, get } from "svelte/store";

const _isEmergencyMode = writable(false);

export const emergencyStore = {
  subscribe: _isEmergencyMode.subscribe,
  get isEmergencyMode() { return get(_isEmergencyMode); },
  set isEmergencyMode(v) { _isEmergencyMode.set(v); },
};
