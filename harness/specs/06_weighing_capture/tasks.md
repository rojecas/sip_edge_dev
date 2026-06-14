# Tasks — Captura de Pesaje Multipaso con Confirmacion y Envio RS232

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.

---

- [x] T1 — Anadir modelo ORM `Weighing` en `src/models.py` con todos los
      campos especificados en el design (`fecha`, `hora`, `tractomula`,
      `vagon`, `numero_guia`, `hacienda_id`, `suerte_id`, `peso_muestra`,
      `peso_mineral`, `peso_vegetal_extrano`, `usuario_id`, `created_at`,
      `enviado_pc`) y FKs correspondientes. Cubre: R3, R21, R22.

- [x] T2 — Crear `src/weighings.py` con esquemas Pydantic `WeighingCreate`,
      `WeighingResponse`, `ResetResponse`. Cubre: R3, R20, R21, R22.

- [x] T3 — Anadir helper `require_any_role(*roles)` en `src/auth.py` para
      permitir multiples roles en un dependency. Cubre: R1, R2, R9, R10, R11.

- [x] T4 — Implementar endpoint `POST /api/weighings` en `src/weighings.py`
      con validacion: fecha/hora auto, usuario_id auto, FK checks,
      transaccion atomica, RS232 stub. Cubre: R3, R4, R5, R6, R7, R8, R9,
      R20, R21, R22, R23.

- [x] T5 — Implementar endpoint `GET /api/weighings` con filtro por rol
      (admin ve todos, operator ve propios). Cubre: R10, R11.

- [x] T6 — Implementar endpoint `GET /api/weighings/{id}` con visibilidad
      segun rol. Cubre: R12, R13, R14, R15.

- [x] T7 — Implementar endpoint `POST /api/weighings/reset` que devuelve
      confirmacion. Cubre: R16.

- [x] T8 — Registrar `weighings_router` en `src/main.py` con import de
      `Weighing` en los modelos. Cubre: R3.

- [x] T9 — Refactorizar `src/haciendas.py` / `src/main.py` para exponer
      endpoints GET de haciendas y suertes con `require_any_role("admin",
      "operator")`. Los endpoints write (POST, PUT, DELETE) permanecen
      admin-only. Cubre: R1, R2.

- [x] T10 — Implementar WebSocket endpoint `WS /ws/scale` en `src/main.py`
      con autenticacion via query param `token`, set de clientes, y
      callback de ScaleService que difunde lecturas. Cubre: R17, R18, R19.

- [x] T11 — Implementar stub de `send_frame` (try/except ImportError) en
      `POST /api/weighings` que establece `enviado_pc` segun exito/fallo.
      Cubre: R4, R7, R23.

- [x] T12 — Crear `tests/test_weighings.py` con helper `_build_test_app`
      (mismo patrón que `test_haciendas.py`) que incluye seed de operador
      y admin. Cubre: verificacion general.

- [x] T13 — Test: `POST /api/weighings` como operador crea registro
      exitosamente con fecha/hora auto y usuario_id auto. Cubre: R3, R5, R21, R22.

- [x] T14 — Test: `POST /api/weighings` con peso negativo devuelve HTTP 422.
      Cubre: R20.

- [x] T15 — Test: `POST /api/weighings` sin token devuelve HTTP 401.
      Cubre: R8.

- [x] T16 — Test: `POST /api/weighings` como admin funciona correctamente.
      Cubre: R9.

- [x] T17 — Test: `GET /api/weighings` como operador solo ve sus registros.
      Cubre: R10.

- [x] T18 — Test: `GET /api/weighings` como admin ve todos los registros.
      Cubre: R11.

- [x] T19 — Test: `GET /api/weighings/{id}` como operador ve su propio
      registro. Cubre: R12.

- [x] T20 — Test: `GET /api/weighings/{id}` como operador NO ve registro
      de otro operador (HTTP 404). Cubre: R15.

- [x] T21 — Test: `GET /api/weighings/{id}` como admin ve registro de
      cualquier usuario. Cubre: R13.

- [x] T22 — Test: `GET /api/weighings/9999` devuelve HTTP 404.
      Cubre: R14.

- [x] T23 — Test: `POST /api/weighings/reset` devuelve mensaje de
      confirmacion. Cubre: R16.

- [x] T24 — Test: `POST /api/weighings` con RS232 stub (ImportError)
      continua sin error, `enviado_pc = FALSE`. Cubre: R23.

- [x] T25 — Test: `GET /api/haciendas` como operador devuelve lista
      (no 403). Cubre: R1.

- [x] T26 — Test: `GET /api/suertes?hacienda_id=X` como operador
      devuelve lista. Cubre: R2.

- [x] T27 — Test: WebSocket `/ws/scale` con token valido acepta conexion
      y recibe mensajes. Cubre: R17, R18.

- [x] T28 — Test: WebSocket `/ws/scale` sin token cierra con codigo 4001.
      Cubre: R19.

- [x] T29 — Test: transaccion atomica — validacion FKs previene datos
      invalidos. Cubre: R6.

- [x] T30 — Verificar trazabilidad en `progress/impl_weighing_capture.md`.
      Cubre: todos los R.

- [x] T31 — Ejecutar `docker compose exec backend python -m unittest
      discover -s tests -v` — todo verde. Cubre: verificacion Nivel 1.

- [x] T32 — Ejecutar `./init.ps1` — todos los bloques `[OK]`.
      Cubre: verificacion Nivel 3.
