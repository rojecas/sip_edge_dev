# Tasks — rs232_frame_update

- [ ] T1 — Modificar el bloque `csv_line` en `src/rs232.py:43-54` con el nuevo formato:
  fecha con `/`, hora truncada a HH:MM, campo fijo `1`, pesos `.2f`, 5 ceros de reserva.
  Cubre: R1, R2, R3, R4, R5.

- [ ] T2 — Actualizar `test_csv_format_15_fields` en `tests/test_rs232.py` para
  el nuevo formato de 14 campos: verificar orden y valores de los 14 campos.
  Cubre: R1, R2, R3, R4, R5, R8.

- [ ] T3 — Actualizar `test_pesos_three_decimals` en `tests/test_rs232.py` para
  verificar formato `.2f` en los 3 pesos.
  Cubre: R4, R8.

- [ ] T4 — Agregar `test_fecha_slash_separator` en `tests/test_rs232.py` que
  verifique que la fecha usa `/` como separador (YYYY/MM/DD).
  Cubre: R1, R8.

- [ ] T5 — Agregar `test_hora_no_seconds` en `tests/test_rs232.py` que
  verifique que la hora se transmite sin segundos (HH:MM).
  Cubre: R2, R8.

- [ ] T6 — Agregar `test_campo_fijo_1` en `tests/test_rs232.py` que
  verifique que el campo 5 de la trama contiene el valor fijo `1`.
  Cubre: R3, R8.

- [ ] T7 — Agregar test de integracion en `tests/test_rs232.py` que simule el
  flujo completo (`_build_frame_data` → `send_frame`) y verifique la trama
  resultante con el nuevo formato.
  Cubre: R6, R7, R9.
