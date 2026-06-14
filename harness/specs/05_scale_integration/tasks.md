# Tasks — Integracion Serial con Bascula DINI ARGEO DFWLI-2

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.

---

- [x] T1 — Anadir dataclass `ScaleConfig` en `src/config.py` con
      `timeout_seconds: int` y constante `DEFAULT_SCALE_TIMEOUT = 3`.
      Modificar `load_config` para retornar `tuple[SystemConfig,
      SessionConfig, ScaleConfig]`, leyendo `scale.timeout_seconds`
      desde YAML con validacion 1–10. Anadir `save_scale_config`.
      Cubre: R13, R14.

- [x] T2 — Actualizar callers de `load_config` en `src/main.py`
      (lifespan) para recibir el tercer elemento `ScaleConfig`.
      Cubre: R1.

- [x] T3 — Crear `src/scale.py` con excepciones: `ScaleConnectionError`,
      `ScaleTimeoutError`, `ScaleProtocolError`. Cubre: R9, R10.

- [x] T4 — Implementar `parse_extended_response` y `parse_short_response`
      en `src/scale.py`. Cubre: R7, R8.

- [x] T5 — Implementar clase `ScaleService` con `__init__`,
      `start()`, `stop()`, `send_command()`. Incluir `threading.Lock`
      para escritura serial y `queue.Queue` para datos entrantes.
      Cubre: R1, R2, R3, R4, R5, R6, R9, R10, R11.

- [x] T6 — Implementar `async_listener(callback)` y el hilo daemon
      de background para lectura de datos espontaneos.
      Cubre: R11, R12.

- [x] T7 — Registrar `ScaleService` singleton en lifespan de
      `src/main.py` (start al inicio, stop al apagar). Guardar en
      `app.state.scale_service`. Cubre: R1.

- [x] T8 — Anadir endpoint `PUT /api/setup/scale` en `src/main.py`
      con `ScaleTimeoutRequest` Pydantic schema (Field ge=1, le=10),
      protegido con `check_inactivity` + `require_role("admin")`.
      Cubre: R13, R14, R15, R16.

- [x] T9 — Anadir `update_timeout` method en `ScaleService` para
      cambiar timeout en caliente tras PUT exitoso.
      Cubre: R13.

- [x] T10 — Crear `tests/test_scale.py` con `TestParseExtendedResponse`:
      `test_parse_extended_stable`, `test_parse_extended_unstable`,
      `test_parse_short_response`, `test_parse_invalid_response`.
      Cubre: R7, R8, R10.

- [x] T11 — Tests de `ScaleService.send_command` con mock serial:
      `test_send_rext`, `test_send_tare`, `test_send_tman`,
      `test_send_zero`, `test_send_clear`.
      Cubre: R2, R3, R4, R5, R6.

- [x] T12 — Tests de timeout: `test_send_command_timeout` con mock
      que no responde. Cubre: R9.

- [x] T13 — Tests de async listener: `test_async_listener_receives_data`
      con mock serial que envia linea espontanea.
      Cubre: R11, R12.

- [x] T14 — Tests de endpoint PUT scale config:
      `test_put_scale_config_valid`, `test_put_scale_config_invalid`,
      `test_put_scale_config_unauthorized` (sin token),
      `test_put_scale_config_forbidden` (rol operator).
      Cubre: R13, R14, R15, R16.

- [x] T15 — Verificar trazabilidad en `progress/impl_scale_integration.md`.
      Cubre: todos los R.

- [x] T16 — Ejecutar `docker compose exec backend python -m unittest
      discover -s tests -v` — todo verde. Cubre: verificacion Nivel 1.

- [x] T17 — Ejecutar `./init.ps1` — todos los bloques `[OK]`.
      Cubre: verificacion Nivel 3.
