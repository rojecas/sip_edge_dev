# Closure — Sesion 2026-07-03

> Features trabajadas: 24 (reset_individual_pesos), 25 (virtual_scale)
> Depuracion: envio SMS, SMSC, script send_sms.sh

## Resumen

### Feature 24 — reset_individual_pesos ? DONE

| Etapa | Estado |
|-------|--------|
| Spec | Aprobado por humano |
| Implementacion | 9 tasks [x], 2 bugs corregidos (Body(None), bindable) |
| Review | 2 rondas, aprobado |
| Tests manuales | Aprobados por humano |
| Release | Registrado en tracker (#24) |

### Feature 25 — virtual_scale ?? TESTING

| Etapa | Estado |
|-------|--------|
| Spec | Aprobado por humano |
| Implementacion | 22 tasks [x], 47 tests |
| Review | 3 rondas, aprobado |
| Tests manuales | Pendientes de hardware (conversor RS232/RS485) |
| Release | Pendiente |

### Depuracion de envio SMS

| Hallazgo | Detalle |
|----------|---------|
| Sintaxis mmcli | `--messaging-create-sms "props"` (argumento separado, NO con `=`) |
| SMSC obligatorio | Sin `smsc='+573003690025'` el SMS no llega aunque mmcli diga "sent" |
| Saltos de linea | Scripts bash requieren LF, no CRLF |
| Script reparado | `/usr/local/bin/send_sms.sh` actualizado |
| Documentacion | `docs/sms_mmcli_guide.md` creada en local y EdgeBox |

## Archivos modificados/creados

### Feature 24
- `src/weighings.py` — Schema ResetFieldRequest, Body(None), endpoint /reset
- `frontend/src/components/WeightField.svelte` — bindable, boton Reset
- `frontend/src/components/KioskForm.svelte` — 3 manejadores individuales, Limpiar todo
- `tests/test_weighings.py` — 4 tests
- `frontend/src/components/__tests__/WeightField.test.js` — 3 tests
- `frontend/src/components/__tests__/KioskForm.test.js` — 3 tests (R3)

### Feature 25
- `src/tools/virtual_scale.py` — Servidor serial + REPL
- `scripts/generate_readings.py` — Generador de datasets
- `data/readings/dataset_A-E.csv` — 5 datasets
- `docs/virtual_scale_setup.md` — Documentacion de conexion
- `tests/test_virtual_scale.py` — 47 tests
- `compose.yml` — Volumes data/ y scripts/ anadidos

### Depuracion SMS
- `docs/sms_mmcli_guide.md` — Guia de envio SMS con mmcli
- `/usr/local/bin/send_sms.sh` (EdgeBox) — Script reparado

## Pendientes

1. Feature 25: pruebas manuales con hardware (conversor RS232/RS485)
2. Feature 27: desplegar migraciones SQL + pruebas en EdgeBox
3. Feature 28: depende de Feature 27
4. Bug 26: diagnosticado, pendiente de fix
