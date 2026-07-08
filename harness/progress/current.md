# Sesion actual - 2026-07-08

- **Inicio:** 2026-07-08
- **Agente:** leader (deepseek-v4-pro)
- **Enfoque:** Pruebas manuales Feature 25 - Balanza Virtual (virtual_scale)

## Resumen de la sesion

### Feature 25 — Balanza Virtual (VERIFICADA → DONE)
- **Fix aplicado:** Error `select.select()` en Windows corregido (separar path msvcrt de fallback Unix)
- **Pruebas realizadas:**
  - Comunicacion RS-485 real a 9600 baud: ✅ REXT, TARE, ZERO, CLEAR, TMAN responden OK
  - Integracion con sip-edge via RS-485: ✅ 5/5 comandos desde EdgeBox
  - REPL interactivo: ✅ navegacion n/p/w/g/s/q/espacio
  - 5 datasets disponibles: ✅
- **Bug descubierto en sip-edge (scale.py + main.py):**
  - `_async_reader` crashea con TypeError, no se recupera
  - `_on_scale_data` no await correctamente `ws.send_text()` en WebSocket
  - `ScaleService` inicia pero no loggea "started"
- **config.yaml cambiado a 9600 baud** (default de balanza DINI ARGEO)

## Pendientes
| Item | Status | Nota |
|------|--------|------|
| Bug 26 (emergency_request_wrong_sms) | triaged | Bug-fixer pendiente |
| F27 (sms_persistence) | testing | Espera pruebas manuales + autorizacion |
| F28 (ai_multi_turn) | pending | Pendiente spec-author |
| Bug ScaleService/WebSocket (nuevo) | pending | Bugs descubiertos durante pruebas F25 |
