# Spec Review â€” Feature 13 (frontend_login_kiosk)

## Resumen
- Fecha: 2026-07-09
- Validador: spec-validator (variante B: auditor + corrector)
- Estado anterior del spec: spec_ready (con gaps ERS conocidos)
- Estado despuÃ©s: approved (spec corregido)

## Trazabilidad ERS â†’ R<n>

| RF | R<n> que lo cubre | Estado |
|----|-------------------|--------|
| RF-F13-01 | R1, R2, R4, R30, R41, R42 | âœ… |
| RF-F13-02 | R2, R3, R33 | âœ… |
| RF-F13-03 | R10, R11, R34 | âœ… |
| RF-F13-04 | R14, R15 (corregido), R16 (corregido), R32, R40 | âœ… |
| RF-F13-05 | R15 (corregido), R17, R18, R35, R45 | âœ… |
| RF-F13-06 | R19, R20, R21 | âœ… |
| RF-F13-07 | R22, R37, R38, R39 | âœ… |
| RF-F13-08 | R23, R24, R25 | âœ… |
| RF-F13-09 | R26, R27, R28 | âœ… |
| RF-F13-10 | R5, R6, R7, R8, R9 | âœ… |
| RF-003 (comando REXT/TARE) | R15 (corregido), R16 (corregido), R43 (nuevo) | âœ… |
| RF-003 (timeout configurable) | â€” (implementado en ScaleService, fuera del alcance frontend) | âœ… |
| RF-003 (PRINT auto-capture) | R44 (nuevo) | âœ… |
| RF-003 (ScaleService singleton) | R43 (nuevo) | âœ… |

## Hallazgos

1. **R15 incorrecto** â†’ El spec decÃ­a "tomar valor del WebSocket" pero RF-003 exige enviar comando REXT al RS485. Se corrigiÃ³ R15 para usar `POST /api/scale/command` con `{command: "REXT"}`.
2. **R16 sin implementar** â†’ El spec era correcto ("enviar comando de tara a la bÃ¡scula via API") pero la implementaciÃ³n solo hacÃ­a `value = 0` local sin llamar a la bÃ¡scula. Se corrigiÃ³ R16 para usar `POST /api/scale/command` con `{command: "TARE"}`.
3. **Auto-capture PRINT faltante** â†’ RF-003 exige "escucha asÃ­ncrona de datos entrantes desde la balanza (botÃ³n PRINT)". No existÃ­a en el spec original. Se agregÃ³ R44 nuevo.
4. **Sin endpoint de comandos de bÃ¡scula** â†’ No existÃ­a endpoint intermedio. Se agregÃ³ R43 nuevo y `src/scale_api.py`.
5. **No hay separaciÃ³n de responsabilidades** â†’ El spec no diferenciaba entre WebSocket (monitoreo pasivo) y comando HTTP (lectura activa). Se documentÃ³ en design.md como alternativa descartada.
6. **R45** â†’ Se agregÃ³ requirement para garantizar que el indicador de peso en vivo no se vea afectado por los cambios.

## Archivos modificados
- requirements.old.md â†’ renombrado
- requirements.md â†’ corregido (R15, R16 actualizados; R43, R44, R45 agregados)
- design.old.md â†’ renombrado
- design.md â†’ actualizado (nuevo endpoint, auto-capture, secciÃ³n de impacto, alternativa descartada)
- tasks.old.md â†’ renombrado
- tasks.md â†’ actualizado (T22 corregido; T36-T43 nuevos)

## Archivos nuevos requeridos (para implementer)
- `src/scale_api.py` â†’ endpoint `POST /api/scale/command`

## Archivos a modificar (para implementer)
- `frontend/src/components/WeightField.svelte` â†’ Leer/Tara llaman API
- `frontend/src/components/KioskForm.svelte` â†’ auto-capture PRINT
- `frontend/src/lib/ws.js` â†’ exportar `onScaleReading` callback
- `frontend/src/lib/constants.js` â†’ anadir `SCALE_COMMAND` endpoint
- `src/main.py` â†’ incluir scale_router
- `tests/` â†’ tests para endpoint y auto-capture

