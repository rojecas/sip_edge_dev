# Tasks — Frontend Admin: Configuración y Backup

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.
> NOTA: El codigo fuente ya existe del desarrollo de feature 14. Estas tasks
> verifican su correcto funcionamiento y corrigen problemas conocidos.

---

## Fase 1 — Verificacion de AdminConfig (/admin/config)

- [ ] T1 — Verificar que `AdminConfig.svelte` carga configuracion al montar:
  - Llama `GET /api/config`
  - Pre-puebla todos los campos (RS485, RS232, GSM, timeouts)
  - Muestra indicador de carga mientras carga
  - Muestra mensaje de error si la carga falla
  Cubre: R2, R6.

- [ ] T2 — Verificar secciones del formulario de configuracion:
  - Seccion RS485 con campos: path (text), baudrate (select 10 valores),
    parity (select 5 valores), data_bits (select 4 valores), stop_bits (select 3 valores)
  - Seccion RS232 con misma estructura
  - Seccion GSM con campo modem_index (number)
  - Todos los selects usan valores predefinidos (R11)
  Cubre: R1, R11.

- [ ] T3 — Verificar guardado de configuracion:
  - Boton "Guardar Configuracion" envia `PUT /api/config` con JSON completo
  - HTTP 200 → muestra "Configuracion guardada exitosamente"
  - HTTP 422 → muestra error SIN perder cambios del formulario
  Cubre: R3.

- [ ] T4 — Verificar prueba de puertos:
  - Cada boton Test (RS485, RS232, GSM) llama `POST /api/config/test/{port}`
  - Boton se deshabilita y muestra "Probando..." durante la peticion
  - `"status": "ok"` → mensaje verde "Prueba exitosa"
  - `"status": "fail"` → mensaje rojo con detalle del error
  - Error de red → mensaje generico
  Cubre: R4.

- [ ] T5 — Verificar guardado de timeouts:
  - Boton "Guardar Session Timeout" envia `PUT /api/setup/session`
  - Boton "Guardar Scale Timeout" envia `PUT /api/setup/scale`
  - Cada boton tiene su propio estado de submitting
  - Mensajes de exito/error individuales
  Cubre: R5.

## Fase 2 — Verificacion de AdminBackup (/admin/backup)

- [ ] T6 — Verificar que `AdminBackup.svelte` carga historial al montar:
  - Llama `GET /api/backup/status`
  - Extrae correctamente `.items` de la respuesta (problema conocido)
  - Muestra tabla con columnas: ID, Archivo, Tamano, Checksum Local,
    Copia USB, Checksum USB, Error, Fecha
  - Mensaje "No hay registros de backup" si lista vacia
  - Indicador de carga mientras carga
  Cubre: R7.

- [ ] T7 — Verificar ejecucion de backup:
  - Boton "Ejecutar Backup" envia `POST /api/backup/run`
  - HTTP 202 → muestra "Backup iniciado en segundo plano"
  - Boton deshabilitado por 30s con "Procesando..." + spinner
  - HTTP 4xx/5xx → muestra error, NO deshabilita boton
  Cubre: R8, R9.

- [ ] T8 — Verificar boton "Refrescar":
  - Recarga la tabla via `GET /api/backup/status`
  - No duplica registros
  Cubre: R10.

## Fase 3 — Build y verificacion

- [ ] T9 — Ejecutar `npm run build` en `frontend/`:
  - Sin errores de compilacion
  Cubre: verificacion Nivel 1.

- [ ] T10 — Copiar `frontend/dist/*` a `src/static/`:
  - Archivos copiados correctamente
  Cubre: verificacion despliegue.

- [ ] T11 — Ejecutar `./init.ps1`:
  - Todos los bloques `[OK]`
  Cubre: verificacion Nivel 3.

- [ ] T12 — Verificar trazabilidad completa en `progress/impl_frontend_admin_operations.md`:
  - Mapear cada `R<n>` a su test o verificacion manual
  Cubre: trazabilidad.
