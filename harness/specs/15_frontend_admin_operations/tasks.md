# Tasks — Frontend Admin: Configuración y Backup

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.
> NOTA: El codigo fuente ya existe del desarrollo de feature 14. Estas tasks
> verifican su correcto funcionamiento y corrigen problemas conocidos.

---

## Fase 1 — Verificacion de AdminConfig (/admin/config)

- [x] T1 — Verificar que `AdminConfig.svelte` carga configuracion al montar:
  - Llama `GET /api/config`
  - Pre-puebla todos los campos (RS485, RS232, GSM, timeouts)
  - Muestra indicador de carga mientras carga
  - Muestra mensaje de error si la carga falla
  Cubre: R2, R6.

- [x] T2 — Verificar secciones del formulario de configuracion:
  - Seccion RS485 con campos: path (text), baudrate (select 10 valores),
    parity (select 5 valores), data_bits (select 4 valores), stop_bits (select 3 valores)
  - Seccion RS232 con misma estructura
  - Seccion GSM con campo modem_index (number)
  - Todos los selects usan valores predefinidos (R11)
  Cubre: R1, R11.

- [x] T3 — Verificar guardado de configuracion:
  - Boton "Guardar Configuracion" envia `PUT /api/config` con JSON completo
  - HTTP 200 → muestra "Configuracion guardada exitosamente"
  - HTTP 422 → muestra error SIN perder cambios del formulario
  Cubre: R3.

- [x] T4 — Verificar prueba de puertos:
  - Cada boton Test (RS485, RS232, GSM) llama `POST /api/config/test/{port}`
  - Boton se deshabilita y muestra "Probando..." durante la peticion
  - `"status": "ok"` → mensaje verde "Prueba exitosa"
  - `"status": "fail"` → mensaje rojo con detalle del error
  - Error de red → mensaje generico
  Cubre: R4.

- [x] T5 — Verificar guardado de timeouts:
  - Boton "Guardar Session Timeout" envia `PUT /api/setup/session`
  - Boton "Guardar Scale Timeout" envia `PUT /api/setup/scale`
  - Cada boton tiene su propio estado de submitting
  - Mensajes de exito/error individuales
  Cubre: R5.

## Fase 2 — Verificacion de AdminBackup (/admin/backup)

- [x] T6 — Verificar que `AdminBackup.svelte` carga historial al montar:
  - Llama `GET /api/backup/status`
  - Extrae correctamente `.items` de la respuesta (fallback: `result.items || result || []`)
  - Muestra tabla con columnas: ID, Archivo, Tamano, Checksum Local,
    Copia USB, Checksum USB, Error, Fecha
  - Mensaje "No hay registros de backup" si lista vacia
  - Indicador de carga mientras carga
  Cubre: R7.

- [x] T6a — Corregir field name mismatch en `AdminBackup.svelte`:
  - Backend retorna: `filename`, `file_size`, `local_checksum`, `usb_copied`,
    `usb_checksum`, `error_message`, `created_at`
  - Frontend usa: `archivo`, `tamano`, `checksum_local`, `copia_usb`,
    `checksum_usb`, `error`, `fecha`
  - Mapear campos ingles → español en el script del componente
  - Verificar que la tabla muestra valores reales (no "—") cuando hay registros
  Cubre: R7.

- [x] T7 — Verificar ejecucion de backup:
  - Boton "Ejecutar Backup" envia `POST /api/backup/run`
  - HTTP 202 → muestra "Backup iniciado en segundo plano"
  - Boton deshabilitado por 30s con "Procesando..." + spinner
  - HTTP 4xx/5xx → muestra error, NO deshabilita boton
  Cubre: R8, R9.

- [x] T8 — Verificar boton "Refrescar":
  - Recarga la tabla via `GET /api/backup/status`
  - No duplica registros
  Cubre: R10.

## Fase 3 — Build y verificacion

- [x] T9 — Ejecutar `npm run build` en `frontend/`:
  - Sin errores de compilacion
  Cubre: verificacion Nivel 1.

- [x] T10 — Copiar `frontend/dist/*` a `src/static/`:
  - Archivos copiados correctamente
  Cubre: verificacion despliegue.

- [x] T11 — Ejecutar `./init.ps1`:
  - Todos los bloques `[OK]`
  Cubre: verificacion Nivel 3.

- [x] T12 — Verificar trazabilidad completa en `progress/impl_frontend_admin_operations.md`:
  - Mapear cada `R<n>` a su test o verificacion manual
  Cubre: trazabilidad.

## Fase 4 — Tests de frontend (Vitest + Testing Library)

- [x] T13 — Configurar Vitest en frontend/:
  - Instalar itest, @testing-library/svelte, @testing-library/jest-dom, jsdom
  - Crear rontend/vitest.config.js (extiende vite.config.js)
  - Agregar script "test": "vitest run" en package.json
  - Crear rontend/src/setupTest.js con setup de testing-library
  Cubre: infraestructura de tests frontend.

- [x] T14 — Escribir tests para AdminConfig.svelte:
  - rontend/src/components/__tests__/AdminConfig.test.js
  - Test: carga config al montar (mock GET /api/config, verificar campos pre-poblados)
  - Test: muestra indicador de carga mientras loading=true
  - Test: muestra error si carga falla
  - Test: guardar config llama PUT /api/config
  - Test: test de puerto muestra resultado verde/rojo
  Cubre: R1, R2, R3, R4, R5, R6, R11.

- [x] T15 — Escribir tests para AdminBackup.svelte:
  - rontend/src/components/__tests__/AdminBackup.test.js
  - Test: carga historial al montar (mock GET /api/backup/status)
  - Test: renderiza tabla con datos reales (verifica field names corregidos: filename, file_size, etc.)
  - Test: muestra "No hay registros de backup" si lista vacia
  - Test: ejecutar backup llama POST /api/backup/run y deshabilita 30s
  - Test: error 4xx/5xx no deshabilita boton
  - Test: boton Refrescar recarga tabla
  Cubre: R7, R8, R9, R10.

- [x] T16 — Ejecutar tests frontend y verificar:
  - cd frontend && npx vitest run — todos los tests pasan
  Cubre: verificacion tests frontend.

- [x] T17 — Ejecutar 
pm run build en rontend/:
  - Sin errores de compilacion (confirmar que los tests no rompieron el build)
  Cubre: verificacion post-tests.

- [x] T18 — Actualizar progress/impl_frontend_admin_operations.md:
  - Agregar seccion de tests frontend con resultados
  - Actualizar trazabilidad con los nuevos tests (T14-T15 cubren R1-R11)
  - Documentar skills consultados (svelte5 ya documentado)
  Cubre: trazabilidad completa.
