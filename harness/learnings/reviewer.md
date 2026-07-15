# Lecciones para el Reviewer

## Sesion 2026-07-14/15 — F28 ai_multi_turn
- Verificar que el dispatcher no descarte SMS entrantes por deteccion de auto-generados falsa.
- Verificar que las pruebas en el EdgeBox incluyan el flujo completo: envio via mmcli -> recepcion via dispatcher -> procesamiento del handler.
- Verificar que init.ps1 corra con timeout suficiente (3min para tests completos).
