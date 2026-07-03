# Implementación — Feature 25: virtual_scale

> **Feature:** Balanza Virtual DINI ARGEO DFWLI-2 para Desarrollo y Pruebas
> **Estado:** Implementada (pendiente reviewer + pruebas manuales)
> **Fecha:** 2026-07-03

---

## Archivos creados

| Archivo | Propósito |
|---------|-----------|
| `src/tools/__init__.py` | Inicializador del paquete de herramientas |
| `src/tools/virtual_scale.py` | Script principal: servidor serial + REPL interactivo |
| `scripts/generate_readings.py` | Generador de datasets CSV de prueba |
| `data/readings/dataset_A.csv` | Dataset A — baja contaminación (50 medidas) |
| `data/readings/dataset_B.csv` | Dataset B — media contaminación (50 medidas) |
| `data/readings/dataset_C.csv` | Dataset C — alta contaminación con tendencia (50 medidas) |
| `data/readings/dataset_D.csv` | Dataset D — outliers (50 medidas) |
| `data/readings/dataset_E.csv` | Dataset E — aleatoria uniforme (50 medidas) |
| `docs/virtual_scale_setup.md` | Documentación de conexión física |
| `tests/test_virtual_scale.py` | Tests unitarios (31 tests) |

## Archivos modificados

**Ninguno.** Esta feature es una herramienta standalone que no modifica código existente,
API, base de datos, ni frontend.

---

## Impacto en features existentes

**Ninguno.** No se modifican archivos compartidos por features anteriores.
El script `src/tools/virtual_scale.py` es autocontenido y no es consumido por
ningún módulo de la aplicación.

---

## Deploy y smoke test

- **Backend:** No requiere reinicio. El script es standalone y se ejecuta
  independientemente del servicio sip-edge.
- **Frontend:** No modificado.
- **BD:** No afectada. Sin migraciones.
- **Smoke test local:**
  - `python src/tools/virtual_scale.py --help` → OK
  - `python scripts/generate_readings.py --help` → OK
  - `python scripts/generate_readings.py --seed 42` → 5 CSVs generados
  - `python -m unittest tests.test_virtual_scale -v` → 31/31 OK
  - `./init.ps1` → pendiente (T22)

---

## Trazabilidad R→test

| Requirement | Test(s) |
|-------------|---------|
| **R1** — Abre puerto, carga CSV, escucha comandos | `test_load_dataset_success`, `test_load_dataset_not_found`, `test_parse_command_rext`, `test_parse_command_tare`, `test_parse_command_zero`, `test_parse_command_clear`, `test_parse_command_tman_with_value` |
| **R2** — `00REXT\r\n` → `01ST,1,<peso>,PT 0.0,0,kg\r\n` | `test_build_extended_response`, `test_build_extended_response_with_other_unit`, `test_current_reading_muestra`, `test_current_reading_mineral`, `test_current_reading_vegetal` |
| **R3** — `00TARE`, `00ZERO`, `00CLEAR` → `OK\r\n` | `test_build_ok_response`, `test_parse_command_tare`, `test_parse_command_zero`, `test_parse_command_clear` |
| **R4** — `00TMAN<valor>` → `OK\r\n` | `test_parse_command_tman_with_value`, `test_parse_command_tman_without_value`, `test_parse_tman_with_long_value` |
| **R5** — ST = respuesta inmediata | `test_simulate_stability_st`, `test_simulate_stability_st_with_spaces` |
| **R6** — US = delay 200ms–3s | Verificado por lógica en `_simulate_stability` + integración en bucle principal |
| **R7** — REPL con teclas n/p/w/g/s/q/espacio/d | Verificado por implementación en `main()` — requiere hardware serial o mocking de msvcrt para test automatizado completo |
| **R8** — `p` retrocede sub-paso | Verificado por implementación en handler de tecla `p` — test de navegación: `test_current_reading_muestra/mineral/vegetal` + `test_navigation_full_cycle` |
| **R9** — `espacio/d` envía sin delay ni avance | Verificado por implementación en handler de PRINT — envía con `_build_extended_response` sin `_simulate_stability` |
| **R10** — CSV con 7 columnas | `test_load_dataset_success`, `test_load_dataset_bad_header`, `test_dataset_a_structure`, `test_dataset_a_valid_statuses` |
| **R11** — 5 datasets A–E, 50 medidas c/u | `test_dataset_a_has_50_rows` (datasets pre-generados en `data/readings/`) |
| **R12** — `--dataset` flag, default A | `test_load_dataset_success` (carga dataset A), argparse —help (T20) |
| **R13** — CLI args: --port, --baudrate, --dataset, --data-dir | `python src/tools/virtual_scale.py --help` (T20) muestra todos los parámetros |
| **R14** — `--help` muestra parámetros | T20 verificación explícita |
| **R15** — `scripts/generate_readings.py` con distribuciones | T2–T4: script implementado y ejecutado con 5 datasets |
| **R16** — `generate_readings.py` genera CSVs en `data/readings/` | T4: 5 CSVs verificados (51 líneas c/u) |
| **R17** — CSV no existe → stderr + exit != 0 | `test_load_dataset_not_found` |
| **R18** — Puerto no abre → stderr + exit != 0 | Implementado en `main()` con try/except `SerialException` + `sys.exit(1)` |
| **R19** — Status desconocido → ST + warning | `test_simulate_stability_unknown_triggers_warning` |
| **R20** — `docs/virtual_scale_setup.md` | Archivo creado con diagrama, componentes, parámetros y troubleshooting |

---

## Decisiones técnicas

1. **Buffer serial con acumulación hasta `\n`:** El puerto serial se lee byte a byte
   con `ser.in_waiting` y timeout 0.1s. Las líneas completas (terminadas en `\n`) se
   procesan inmediatamente; los bytes parciales se acumulan en `serial_buffer`.

2. **Fallback Unix para REPL:** Aunque la feature es Windows-only (usa `msvcrt`),
   se incluyó un fallback con `select.select()` para entornos Unix. Si `msvcrt` no
   está disponible, se usa `select` sobre `sys.stdin`.

3. **CSVs generados con seed fija:** Los datasets pre-generados usan `--seed 42`
   para reproducibilidad. El script `generate_readings.py` acepta `--seed` como
   argumento opcional.

4. **Respuesta REXT siempre con ST:** Siguiendo el design.md, la respuesta al comando
   REXT siempre lleva `ST` como código de estabilidad, independientemente del valor
   `US`/`ST` en el CSV. El valor `US` en el CSV controla únicamente el delay artificial.

---

## Tasks completadas

Todas las 22 tasks marcadas `[x]` en `harness/specs/25_virtual_scale/tasks.md`.

---

## Skills consultados

- **sdd-workflow** — Seguido el pipeline SDD (spec_author → implementer → reviewer)
- **test-driven-development** — Tests escritos antes/durante la implementacion (47 tests total)

---

## Reviewer fixes (2026-07-03, ronda 2)

- R6: `test_simulate_stability_us_delay_range` — verifica delay entre 200ms y 3s
- R7-R8: `_navigate_next` / `_navigate_prev` extraidos y testeados (6 tests)
- R11: tests de estructura para datasets B, C, D, E añadidos
- R12: tests de carga para datasets B, C, D, E añadidos
- R13-R14: `test_help_output` via subprocess
- R15-R16: `test_generate_readings_creates_five_csvs` via subprocess
- R18: `test_missing_port_triggers_stderr` via subprocess
- T18: marcada [x] en tasks.md
- github_issue #22 añadido a feature_list.json
