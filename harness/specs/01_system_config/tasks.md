# Tasks — system_config

> Pasos discretos en orden de implementacion. Cada task referencia los R<n> que cubre.

- [x] T1 — Crear `src/config.py` con dataclasses congelados `SerialPortConfig`,
  `GsmConfig`, `SystemConfig`, constantes de validacion y `default_config()`.
  Cubre: R4, R14.

- [x] T2 — Implementar `load_config()` en `src/config.py`: carga desde YAML con
  fallback a defaults si el archivo no existe o es invalido. Cubre: R3, R4, R16.

- [x] T3 — Implementar `save_config()` en `src/config.py`: serializa a YAML,
  escribe via temp file + `os.replace()`. Cubre: R15.

- [x] T4 — Implementar `validate_config()` en `src/config.py`: valida baudrate,
  parity, data_bits, stop_bits, modem_index contra conjuntos validos. Lanza
  `ValueError`. Cubre: R5, R6, R7, R8, R9.

- [x] T5 — Registrar `GET /api/config` en `src/main.py`: lee config del estado
  global, devuelve JSON con status 200. Cubre: R1.

- [x] T6 — Registrar `PUT /api/config` en `src/main.py`: valida body JSON,
  construye nueva `SystemConfig`, valida con `validate_config()`, persiste con
  `save_config()`, devuelve 200 o 422. Cubre: R2, R5, R6, R7, R8, R9.

- [x] T7 — Registrar `POST /api/config/test/{port}` en `src/main.py` con logica
  de test para rs485 y rs232 usando `pyserial`. Cubre: R10, R11, R13.

- [x] T8 — Registrar logica de test GSM en `POST /api/config/test/gsm` usando
  `subprocess.run(["mmcli", "-m", str(modem_index)])`. Cubre: R12, R13.

- [x] T9 — Anadir `pyserial==3.5` a `requirements.txt`. Cubre: R10, R11.

- [x] T10 — Crear `tests/test_config.py` con `TestSerialPortConfig`:
  `test_creation_defaults`, `test_immutability`. Cubre: R4, R14.

- [x] T11 — Anadir `TestLoadSaveConfig` en `tests/test_config.py`:
  `test_load_defaults_when_no_file`, `test_save_and_load_roundtrip`,
  `test_atomic_write_does_not_corrupt`. Cubre: R3, R4, R15, R16.

- [x] T12 — Anadir `TestValidateConfig` en `tests/test_config.py`:
  `test_invalid_baudrate`, `test_invalid_data_bits`, `test_invalid_parity`,
  `test_invalid_stop_bits`, `test_invalid_modem_index`. Cubre: R5, R6, R7, R8, R9.

- [x] T13 — Anadir `TestConfigEndpoints` en `tests/test_config.py` usando
  `TestClient`:
  `test_get_config_returns_200`, `test_put_config_valid_returns_200`,
  `test_put_config_invalid_baudrate_returns_422`. Cubre: R1, R2, R5.

- [x] T14 — Anadir `TestConfigTestEndpoint` en `tests/test_config.py`:
  `test_test_rs485_serial_attempt`, `test_test_rs232_serial_attempt`,
  `test_test_gsm_mmcli_success`, `test_test_gsm_mmcli_failure`,
  `test_test_invalid_port_returns_404`. Cubre: R10, R11, R12, R13.

- [x] T15 — Ejecutar `docker compose exec backend python -m unittest discover -s
  tests -v` y verificar que todos los tests pasan. Cubre: todos.
