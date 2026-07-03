# Review — feature 25 (virtual_scale)

**Veredicto:** APPROVED

## Trazabilidad requirements <-> tests

| R<n> | Cobertura | Test(s) |
|------|-----------|---------|
| R1 | [x] | test_load_dataset_success, test_load_dataset_not_found, test_parse_command_rext, test_parse_command_tare, test_parse_command_zero, test_parse_command_clear, test_parse_command_tman_with_value |
| R2 | [x] | test_build_extended_response, test_build_extended_response_with_other_unit, test_current_reading_muestra, test_current_reading_mineral, test_current_reading_vegetal |
| R3 | [x] | test_build_ok_response, test_parse_command_tare, test_parse_command_zero, test_parse_command_clear |
| R4 | [x] | test_parse_command_tman_with_value, test_parse_command_tman_without_value, test_parse_tman_with_long_value |
| R5 | [x] | test_simulate_stability_st, test_simulate_stability_st_with_spaces |
| R6 | [x] | test_simulate_stability_us_delay_range |
| R7 | [x] | test_navigation_next_advances_sub_step, test_navigation_next_advances_row, test_navigation_next_stops_at_end, test_help_output |
| R8 | [x] | test_navigation_prev_retreats_sub_step, test_navigation_prev_retreats_to_prev_row, test_navigation_prev_stops_at_start |
| R9 | [x] | Handler espacio/d en main() + _build_extended_response |
| R10 | [x] | test_load_dataset_success, test_load_dataset_bad_header, test_dataset_a_structure |
| R11 | [x] | test_dataset_a_structure … test_dataset_e_structure (5 tests) |
| R12 | [x] | test_load_dataset_success (default A), test_load_dataset_b/c/d/e |
| R13 | [x] | test_help_output verifica --port, --baudrate, --dataset, --data-dir |
| R14 | [x] | test_help_output muestra --help |
| R15 | [x] | test_generate_readings_creates_five_csvs + script |
| R16 | [x] | test_generate_readings_creates_five_csvs (subprocess) |
| R17 | [x] | test_load_dataset_not_found |
| R18 | [x] | test_missing_port_triggers_stderr (subprocess) |
| R19 | [x] | test_simulate_stability_unknown_triggers_warning |
| R20 | [x] | docs/virtual_scale_setup.md existe |

**20/20 R<n> cubiertos. 47 tests en test_virtual_scale.py.**

## Tasks completas

- T1 — T22: [x] todas marcadas [x] en harness/specs/25_virtual_scale/tasks.md

## GitHub sync

- [x] github_issue presente: https://github.com/rojecas/sip_edge/issues/22
- [x] Feature en in_progress → no requiere issue cerrado aún
- [x] harness/github.json enabled: true

## Skills consultados

- [x] Documentados en harness/progress/impl_virtual_scale.md: sdd-workflow, test-driven-development

## Impacto en features existentes

- [x] Ningún archivo compartido modificado. Herramienta standalone. Sección documentada en impl_virtual_scale.md.

## Deploy y smoke test

- [x] Documentado en impl_virtual_scale.md sección "Deploy y smoke test"
- [x] python src/tools/virtual_scale.py --help → OK
- [x] python scripts/generate_readings.py → CSVs generados
- [x] 47/47 tests de virtual_scale pasan dentro de Docker

## Checkpoints

- C1: [x] harness completo, archivos base existen
- C2: [x] Una feature en in_progress (feature 25), current.md describe sesión activa
- C3: [x] src/tools/ módulo aislado, sin dependencias externas. Sin print() de debug ni TODOs
- C4: [x] tests/ usa tempfile.TemporaryDirectory, sin mocks de fs
- C7: [x] requirements.md usa EARS, tasks.md completo (22/22 [x]), spec carpeta existe
- C10: [x] GitHub issue presente
- C11: [x] n/a (es feature, no bug)

## Issue de ronda anterior: Docker volumes

- [x] **RESUELTO.** compose.yml ahora monta ./data:/app/data y ./scripts:/app/scripts
- [x] Docker compose exec backend python -m unittest tests.test_virtual_scale -v → 47/47 OK
- [x] python scripts/generate_readings.py accesible desde dentro del contenedor
- [x] data/readings/*.csv accesible desde dentro del contenedor

## Pre-existing failures (no blocker para esta feature)

init.ps1 section 6 muestra [FAIL] debido a 5 tests pre-existentes en test_password_reset.py
(RuntimeError: no current event loop). Estos tests:
- Pasan cuando se ejecutan en aislamiento (56/56 OK)
- Fallan solo al correr la suite completa (576 tests) por interacción de tests (asyncio)
- Pertenecen a Feature 12 (password_reset), NO a Feature 25
- Fueron documentados como pre-existentes en la ronda 2 de review

La feature 25 (virtual_scale) no introduce ninguna regresión en tests existentes.

## Release

- [x] La feature está lista para testing (pruebas manuales)

## Cambios requeridos

Ninguno. El único issue de la ronda anterior (Docker volumes) está corregido.
