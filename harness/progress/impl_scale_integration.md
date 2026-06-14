# Implementation Report — scale_integration

## Files created
- `src/scale.py` — ScaleService singleton, parsing functions, exception classes
- `tests/test_scale.py` — 30 tests covering all scale features

## Files modified
- `src/config.py` — Added `ScaleConfig` dataclass, `DEFAULT_SCALE_TIMEOUT`, updated `load_config` to return 3-tuple, added `save_scale_config`, updated `_atomic_write_sections` and `_save_system_config_atomic`
- `src/main.py` — Updated lifespan to initialize ScaleService, added `PUT /api/setup/scale` endpoint, added `ScaleTimeoutRequest` schema
- `tests/test_config.py` — Updated all `load_config` call sites to unpack 3 values
- `tests/test_users.py` — Added `ScaleConfig` to app state in test setup
- `harness/specs/05_scale_integration/tasks.md` — All tasks marked `[x]`

## Traceability

| Requirement | Test(s) |
|-------------|---------|
| R1 | `test_put_scale_config_valid` (ScaleService lifecycle in lifespan) |
| R2 | `test_send_rext` |
| R3 | `test_send_tare` |
| R4 | `test_send_tman` |
| R5 | `test_send_zero` |
| R6 | `test_send_clear` |
| R7 | `test_parse_extended_stable`, `test_parse_extended_unstable`, `test_parse_extended_overload` |
| R8 | `test_parse_short_response`, `test_parse_short_stable` |
| R9 | `test_send_command_timeout`, `test_send_command_empty_response_timeout` |
| R10 | `test_parse_invalid_response`, `test_parse_extended_wrong_field_count`, `test_send_command_unknown_command` |
| R11 | `test_async_listener_receives_data` |
| R12 | `test_async_listener_receives_data` |
| R13 | `test_put_scale_config_valid`, `test_save_scale_config_roundtrip` |
| R14 | `test_put_scale_config_invalid_below_range`, `test_put_scale_config_invalid_above_range`, `test_put_scale_config_invalid_type` |
| R15 | `test_put_scale_config_unauthorized` |
| R16 | `test_put_scale_config_forbidden` |

## Verification
- `python -m unittest discover -s tests`: 174 tests OK
- `./init.ps1`: All blocks `[OK]`
