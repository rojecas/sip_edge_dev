# Tasks — rs232_transmission

> Pasos discretos en orden de implementación. Cada task referencia los R<n> que cubre.

- [x] T1 — Crear `src/rs232.py` con la función `send_frame()`. Incluir:
      - Módulo docstring con una línea descriptiva.
      - Constante `_DEV_MODES` para detección de DEV_MODE.
      - Clase `Rs232Error(Exception)` como excepción base.
      - Función `send_frame(frame_data, format="csv", config_path="config.yaml")`.
      - Lógica de DEV_MODE: retornar inmediatamente si está activo. Cubre: R7.
      - Carga de configuración vía `load_config(config_path)`. Cubre: R4.
      - Construcción de línea CSV con 15 campos y CRLF. Cubre: R2, R3, R8, R9, R10.
      - Apertura de puerto serial con `serial.Serial()` usando parámetros del `SystemConfig.rs232`.
      - Escritura de la trama codificada en ASCII.
      - Cierre del puerto serial (en bloque `finally` o `with`).
      - Captura de `serial.SerialException` y relanzamiento como `Rs232Error`.
      - Import local de `serial` dentro de la función (mismo patrón que `src/scale.py`).
      - Las funciones públicas deben tener docstring si tienen más de 5 líneas.

- [x] T2 — Modificar `_send_rs232_frame()` en `src/weighings.py`:
      - Añadir `frame_data["id"] = record.id` antes de llamar a `send_frame()`.
      - Cambiar `format="json"` a `format="csv"` en la llamada a `send_frame()`.
      - Cubre: R1, R5.

- [x] T3 — Crear `tests/test_rs232.py` con clase `TestSendFrame`:
      - `test_csv_format_15_fields`: verificar que la trama generada tiene exactamente
        15 campos separados por coma en el orden correcto. Cubre: R2.
      - `test_vagon_unmodified`: verificar que el valor de `vagon` aparece sin cambios
        en la posición 4 de la trama. Cubre: R3.
      - `test_crlf_termination`: verificar que la trama termina con `\r\n`. Cubre: R8.
      - `test_guia_from_numero_guia`: verificar que `numero_guia` del frame_data aparece
        como campo `Guía` (posición 5). Cubre: R9.
      - `test_pesos_three_decimals`: verificar que los pesos se formatean con 3 decimales.
        Cubre: R10.
      - `test_dev_mode_skips_serial`: con `DEV_MODE=true`, verificar que `send_frame()`
        retorna sin abrir ningún puerto serial. Cubre: R7.
      - `test_config_loaded_and_used`: verificar que `send_frame()` carga la configuración
        desde el archivo YAML y utiliza sus parámetros para el puerto serial.
        Usar `tempfile.TemporaryDirectory()` para crear un `config.yaml` de prueba.
        Cubre: R4.
      - `test_error_on_port_unavailable`: usar mock de `serial.Serial` que lance
        `serial.SerialException`; verificar que `send_frame()` lanza `Rs232Error`.
        Cubre: R6.
      - Usar `unittest.mock.patch` para simular `serial.Serial` donde sea necesario.
      - No usar mocks de sistema de archivos para la configuración; usar archivos
        reales en `tempfile.TemporaryDirectory()`.

- [x] T4 — Modificar `tests/test_weighings.py`:
      - Añadir `test_create_weighing_sends_rs232`: crear un pesaje vía
        `TestClient.post("/api/weighings", ...)`, verificar status 201, luego
        consultar el registro en BD y verificar `enviado_pc == True`.
        Usar mocks para no depender de hardware serial real.
        Cubre: R1, R5.

- [x] T5 — Ejecutar `docker compose exec backend python -m unittest discover -s tests -v`
      y verificar que todos los tests pasan (incluyendo los existentes sin regresión).
      Cubre: todos.
