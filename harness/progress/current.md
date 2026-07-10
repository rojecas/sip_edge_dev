# Sesion cerrada - 2026-07-09 - Feature 13 completada

## Resumen
Sesion dedicada a completar Feature 13 (frontend_login_kiosk):
1. Fase 9: implementacion T36-T43 (scale_api endpoint, REXT/TARE via API, auto-capture PRINT)
2. Correccion de regresion KioskForm ($derived emergencyStore)
3. Refactor scale.py a arquitectura single-reader (4 iteraciones)
4. ScaleReader: indicador de peso neto de cana
5. Documentacion de learnings en AGENTS.md y common.md
6. Cierre formal de F13 y Bug #29

## Entregables

### Codigo
| Archivo | Cambio |
|---------|--------|
| src/scale_api.py | Nuevo: POST /api/scale/command |
| tests/test_scale_api.py | Nuevo: 5 tests unitarios |
| src/scale.py | Refactor: single-reader (async_reader unico lector, send_command escribe y espera Event) |
| WeightField.svelte | Leer/Tara via API (REXT/TARE) + isLoading |
| KioskForm.svelte | Auto-capture PRINT + fix regresion $emergencyStore |
| ws.js | Export onScaleReading callback |
| ScaleReader.svelte | Peso neto cana (muestra - mineral - vegetal) |
| main.py | Import scale_router |

### Harness
| Archivo | Cambio |
|---------|--------|
| AGENTS.md | Paso 9: leer learnings/ al iniciar |
| learnings/common.md | +Secciones 4 (line endings) y 5 (subagentes) |
| .opencode/agents/leader.md | Regla de learnings para subagentes |
| manual_tests_F13.md | 33 pruebas manuales documentadas |
| feature_list.json | F13: done, Bug #29: done, Bug #30: untriaged |

## Lecciones / pitfalls
- Corrupcion de feature_list.json por usar -replace en JSON -> siempre usar Python json.load/dump
- Set-Content sin -Encoding corrompe archivos UTF-8 -> usar Python con encoding explicito
- Line endings: el repo usa LF, verificar antes de modificar con Python
- Subagentes no leen AGENTS.md -> el lider debe instruirles explicitamente sobre learnings/
- scale.py: dos hilos en mismo serial causan condiciones de carrera -> arquitectura single-reader
- sd_notify.py existe pero nunca se llama -> Bug #30

## Pendiente
- Bug #30 (watchdog_sd_notify): agregar tarea asincrona en main.py que llame sd_notify.notify() cada 15s
