# Fix Report — Regression #2 in Feature 13 (KioskForm.svelte)

**Date:** 2026-07-09
**Source:** Reviewer finding in `harness/progress/review_13_frontend_login_kiosk.md` (CRITICAL, Section 3)
**R affected:** R24 (editable fields in emergency mode), R25 (non-editable in normal mode)

## Root Cause

The `$derived(emergencyStore.isEmergencyMode)` pattern was re-introduced during Phase 9 changes (T36-T43). This is identical to the bug fixed on 2026-06-18 (Regression 2: CRITICAL in `impl_frontend_login_kiosk.md`).

`emergencyStore.isEmergencyMode` is a getter that calls `get(_isEmergencyMode)` internally. Svelte 5's `$derived` cannot track `get()` from svelte/store as a reactive dependency. When `_isEmergencyMode.set(v)` runs (via polling in EmergencyBanner), `isEmergencyMode` never updates, so the `disabled` prop on WeightField stays frozen.

## Changes Made

**File:** `frontend/src/components/KioskForm.svelte`

### Change 1 — Delete broken `$derived` line (was line 41)
```diff
-  // Emergency mode — makes weight fields editable
-  let isEmergencyMode = $derived(emergencyStore.isEmergencyMode);
```

### Change 2 — Template: use `$emergencyStore` directly (lines 379-381)
```diff
-      <WeightField ... disabled={!isEmergencyMode} ... />
-      <WeightField ... disabled={!isEmergencyMode} ... />
-      <WeightField ... disabled={!isEmergencyMode} ... />
+      <WeightField ... disabled={!$emergencyStore} ... />
+      <WeightField ... disabled={!$emergencyStore} ... />
+      <WeightField ... disabled={!$emergencyStore} ... />
```

The `$emergencyStore` syntax auto-subscribes to the store (which delegates `subscribe` to `_isEmergencyMode`, a writable). This is reactive — when `_isEmergencyMode.set(v)` runs, the template re-renders.

### Change 3 — handleConfirm(): use `get(emergencyStore)` (line 247)
```diff
-        manual_entry: isEmergencyMode,
+        manual_entry: get(emergencyStore),
```

Added import: `import { get } from "svelte/store";` (line 8).

## Verification

```bash
cd frontend && npm run build
# ✓ built in 1.78s — 0 errors
```

Build copied to `src/static/`.

## Resolution

- R24 (editable fields in emergency mode): ✅ `$emergencyStore` reactively tracks `_isEmergencyMode`, so when emergency mode activates via polling, `disabled={!$emergencyStore}` becomes `disabled={false}`, making WeightField editable.
- R25 (non-editable in normal mode): ✅ In normal mode, `$emergencyStore` is `false`, so `disabled={!false}` = `disabled={true}`, fields are read-only.
