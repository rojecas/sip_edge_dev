# Release Report - Feature 28: ai_multi_turn

**Fecha:** 2026-07-16
**Release:** v1.4.0
**Commit:** 577197a
**Tag:** v1.4.0
**GitHub Release:** https://github.com/rojecas/sip_edge/releases/tag/v1.4.0
**Status:** DONE

## VERSION
- Before: 1.3.1
- After: 1.4.0

## Items released

| ID | Type | Name | Title |
|----|------|------|-------|
| 28 | feature | ai_multi_turn | Conversacion Multiturno para Consultas AI via SMS |
| 29 | bug | scale_service_async_crashes | ScaleService async reader crashes + WebSocket send_text |
| 30 | bug | watchdog_sd_notify | Watchdog mata proceso cada 30s - sd_notify |
| 31 | bug | sms_dispatcher_v2_crashes | Dispatcher v2 crashea en get_user_role_by_phone |

## Tracker
- `harness/releases/tracker.json`: project_version updated to 1.4.0, pending cleared (item 13 stale duplicate removed), new history entry added.

## GitHub
- Release created: https://github.com/rojecas/sip_edge/releases/tag/v1.4.0
- No open GitHub issue for F28 (tracked via feature_list.json + spec directory).
- Issue #12 is closed and belongs to F8 (ai_agent), not F28.

## Testing-phase fixes (commit cac715d)
- conversation_id dispatcher fix: `_dispatch()` reuses active conversation for peer
- SMS sanitization: `_sanitize_sms_text()` truncates to 160 chars, replaces `/` with `-`
- Defense-in-depth: null-checks in password_reset and emergency_mode
- 261 tests green across 8 SMS-adjacent modules
