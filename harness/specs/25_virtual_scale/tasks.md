# Tasks — Balanza Virtual DINI ARGEO DFWLI-2 para Desarrollo y Pruebas

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.

---

- [ ] T1 — Crear estructura de directorios: `src/tools/`, `data/readings/`.
      Cubre: R1, R11.

- [ ] T2 — Implementar `scripts/generate_readings.py` con las 5 funciones generadoras
      (una por dataset A–E) usando `random` de stdlib. Cada dataset debe tener exactamente
      50 filas con las 7 columnas especificadas.
      Cubre: R15, R16.

- [ ] T3 — Agregar `if __name__ == "__main__":` en `scripts/generate_readings.py` con
      argparse para `--output-dir` (default `data/readings/`). Al ejecutarse sin args,
      genera los 5 archivos `dataset_A.csv` a `dataset_E.csv`.
      Cubre: R16.

- [ ] T4 — Ejecutar `python scripts/generate_readings.py` para pre-generar los 5 datasets
      de prueba. Verificar que los 5 archivos CSV existen en `data/readings/` y tienen
      el formato correcto (header + 50 filas, 7 columnas).
      Cubre: R10, R11, R16.

- [ ] T5 — Implementar función `load_dataset(data_dir: str, dataset_id: str) -> list[dict]`
      en `src/tools/virtual_scale.py` que lea el archivo CSV y devuelva una lista de dicts.
      Validar existencia del archivo, header de 7 columnas, y parseo numérico de pesos.
      Cubre: R10, R17.

- [ ] T6 — Implementar función `_current_reading(pointer: tuple[int,int], dataset: list[dict],
      override: float | None) -> dict` que devuelva el dict con `{status, peso, unit}` para
      el sub-paso activo, considerando override si está activo.
      Cubre: R2, R10.

- [ ] T7 — Implementar función `_build_extended_response(reading: dict, address: str) -> str`
      que construya la cadena de respuesta extendida: `01ST,1,<peso>,PT 0.0,0,kg\r\n`.
      Cubre: R2.

- [ ] T8 — Implementar función `_build_ok_response() -> str` que devuelva `OK\r\n`.
      Cubre: R3, R4.

- [ ] T9 — Implementar la clase o funciones `_simulate_stability(status: str) -> None`
      que duerma `random.uniform(0.2, 3.0)` si `status == "US"`, o no duerma si `status == "ST"`.
      Incluir manejo de valores desconocidos con warning en stderr (tratar como ST).
      Cubre: R5, R6, R19.

- [ ] T10 — Implementar el parseador de comandos seriales: dada una línea del puerto,
      detectar si es `00REXT`, `00TARE`, `00TMAN*`, `00ZERO` o `00CLEAR` y enrutar a la
      función de respuesta correspondiente. Ignorar líneas vacías o no reconocidas.
      Cubre: R1, R2, R3, R4.

- [ ] T11 — Implementar el bucle principal del REPL con `msvcrt` para lectura de teclado
      sin Enter. Procesar las teclas: `n`, `p`, `w`, `g`, `s`, `q`, `Espacio`, `d`.
      Cubre: R7, R8, R9.

- [ ] T12 — Implementar el manejador de tecla `n` (next): avanzar sub-paso o fila según
      la lógica del puntero. No avanzar si ya está en la última medida, último sub-paso.
      Cubre: R7.

- [ ] T13 — Implementar el manejador de tecla `p` (previous): retroceder sub-paso o fila
      según la lógica del puntero. No retroceder antes de (fila=0, sub_paso=0).
      Cubre: R7, R8.

- [ ] T14 — Implementar los manejadores de teclas `w` (override peso, solicitar valor
      numérico), `g` (ir a medida, solicitar índice), `s` (mostrar status detallado),
      y `q` (cerrar y salir). La tecla `Espacio`/`d` debe enviar respuesta sin delay
      ni modificación del puntero.
      Cubre: R7, R9.

- [ ] T15 — Implementar la función `show_status()` que muestre: dataset activo, fila actual/
      total filas, sub-paso nombre/índice, peso actual, status del CSV, si hay override activo,
      puerto y baudrate.
      Cubre: R7.

- [ ] T16 — Implementar el bucle principal `main()` con argparse (`--port`, `--baudrate`,
      `--dataset`, `--data-dir`), apertura del puerto serial con manejo de error, carga
      del dataset, y entrada al loop serial/REPL. Capturar `KeyboardInterrupt` para cierre
      limpio. Imprimir mensaje de bienvenida con instrucciones.
      Cubre: R1, R13, R14, R17, R18.

- [ ] T17 — Implementar cierre limpio al recibir `q` o `Ctrl+C`: cerrar puerto serial,
      imprimir mensaje de despedida, salir con código 0.
      Cubre: R7.

- [ ] T18 — Crear `docs/virtual_scale_setup.md` con instrucciones de conexión física,
      componentes necesarios, diagrama de conexión, parámetros de puerto, y procedimiento
      de verificación. Incluir ejemplo de comando de inicio.
      Cubre: R20.

- [ ] T19 — Crear `tests/test_virtual_scale.py` con tests unitarios:
      - `test_load_dataset_success`: carga CSV válido retorna lista de 50 dicts
      - `test_load_dataset_not_found`: archivo inexistente lanza error
      - `test_current_reading_muestra`: pointer (0,0) retorna peso_muestra
      - `test_current_reading_mineral`: pointer (0,1) retorna peso_mineral
      - `test_current_reading_vegetal`: pointer (0,2) retorna peso_vegetal
      - `test_current_reading_override`: override activo retorna peso override
      - `test_build_extended_response`: verifica formato exacto de salida
      - `test_build_ok_response`: verifica "OK\r\n"
      - `test_simulate_stability_st`: ST no produce delay
      - `test_parse_command_rext`: detecta "00REXT\r\n"
      - `test_parse_command_tare`: detecta "00TARE\r\n"
      - `test_parse_command_tman`: detecta "00TMAN1.56\r\n"
      - `test_parse_command_zero`: detecta "00ZERO\r\n"
      - `test_parse_command_clear`: detecta "00CLEAR\r\n"
      Cubre: R2, R3, R4, R5, R10, R17.

- [ ] T20 — Verificar que `python src/tools/virtual_scale.py --help` muestra todos los
      parámetros. Verificar que `python scripts/generate_readings.py` genera los 5 CSVs.
      Cubre: R14, R16.

- [ ] T21 — Verificar que el mapa de trazabilidad R→test se documenta en
      `progress/impl_virtual_scale.md`. Cubre: todos los R.

- [ ] T22 — Ejecutar `./init.ps1` — todos los bloques `[OK]`. Cubre: verificación Nivel 3.
