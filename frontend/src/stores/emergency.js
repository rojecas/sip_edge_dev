/**
 * Emergency mode store — shared reactive state.
 * Used by EmergencyBanner (writer) and KioskForm/WeightField (reader).
 */
let isEmergencyMode = $state(false);

export const emergencyStore = {
  get isEmergencyMode() { return isEmergencyMode; },
  set isEmergencyMode(v) { isEmergencyMode = v; },
};
