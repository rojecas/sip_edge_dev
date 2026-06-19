# Tasks — Frontend: Panel de Administracion

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.

---

## Fase 1 — Preparacion y constantes

- [x] T1 — Anadir nuevos endpoints de API admin en `frontend/src/lib/constants.js`:
  `CONFIG: "/api/config"`, `CONFIG_TEST: "/api/config/test"`,
  `SETUP_SESSION: "/api/setup/session"`, `SETUP_SCALE: "/api/setup/scale"`,
  `USERS: "/api/users"`, `USERS_BY_ID: "/api/users/"`,
  `HACIENDAS: "/api/haciendas"`, `HACIENDAS_BY_ID: "/api/haciendas/"`,
  `SUERTES: "/api/suertes"`, `SUERTES_BY_ID: "/api/suertes/"`,
  `BACKUP_STATUS: "/api/backup/status"`, `BACKUP_RUN: "/api/backup/run"`.
  Cubre: R7, R11, R13, R19, R24, R30.

- [x] T2 — Modificar `frontend/src/App.svelte`:
  - Reemplazar `AdminPlaceholder` con enrutamiento condicional segun
    `currentRoute` para las 6 vistas admin.
  - Importar los nuevos componentes: `AdminDashboard`, `AdminConfig`,
    `AdminUsers`, `AdminHaciendas`, `AdminSuertes`, `AdminBackup`.
  - Default a `AdminDashboard` si la ruta no coincide con ninguna sub-ruta admin.
  - Eliminar import de `AdminPlaceholder`.
  Cubre: R1, R34, R35, R38.

---

## Fase 2 — Layout con sidebar de navegacion

- [x] T3 — Modificar `frontend/src/components/AdminLayout.svelte`:
  - Anadir un sidebar vertical fijo a la izquierda (~220px de ancho) con
    enlaces a: Dashboard, Configuracion, Usuarios, Haciendas, Suertes, Backup.
  - Cada enlace usa `navigate()` del router.
  - La seccion activa se resalta visualmente (background distinto).
  - Mantener el header existente con username + LogoutButton.
  - El sidebar y el header usan las variables CSS existentes (`--bg-secondary`,
    `--text-primary`, etc.) para consistencia visual.
  Cubre: R34.

---

## Fase 3 — Dashboard principal

- [x] T4 — Crear `frontend/src/components/AdminDashboard.svelte`:
  - Grid responsive de 5 cards (Dashboard, Configuracion, Usuarios,
    Haciendas, Suertes, Backup).
  - Cada card tiene: icono, titulo, descripcion breve.
  - Al hacer clic en una card, navega a la ruta correspondiente via
    `router.navigate()`.
  - Estilo: cards con fondo `--bg-secondary`, borde `--border`, hover effect.
  Cubre: R1, R2, R3, R4, R5, R6.

---

## Fase 4 — Configuracion del sistema (/admin/config)

- [x] T5 — Crear `frontend/src/components/AdminConfig.svelte`:
  - Al montar, carga `GET /api/config` y pre-puebla todos los campos.
  - Seccion RS485: campos path (text), baudrate (select), parity (select),
    data_bits (select), stop_bits (select) + boton "Test RS485".
  - Seccion RS232: misma estructura que RS485 + boton "Test RS232".
  - Seccion GSM: campo modem_index (number) + boton "Test GSM".
  - Seccion Timeouts: session_timeout_minutes (number, min 1)
    + boton "Guardar Session Timeout" (PUT /api/setup/session),
    scale_timeout_seconds (number, min 1, max 10)
    + boton "Guardar Scale Timeout" (PUT /api/setup/scale).
  - Boton global "Guardar Configuracion" que envia PUT /api/config con
    el JSON completo de rs485, rs232, gsm.
  - Estados: loading en carga inicial, submitting en cada guardado,
    success/error inline.
  Cubre: R7, R8, R9, R10, R11, R12, R40.

- [x] T6 — Implementar la logica de prueba de puertos en `AdminConfig.svelte`:
  - Cada boton Test (RS485, RS232, GSM) llama
    `POST /api/config/test/{port}` por separado.
  - El boton se deshabilita y muestra "Probando..." mientras la peticion
    esta en curso.
  - Al recibir `"status": "ok"` muestra un mensaje verde "Prueba exitosa"
    junto al boton.
  - Al recibir `"status": "fail"` muestra un mensaje rojo con el detalle
    del error junto al boton.
  - Manejo de errores de red.
  Cubre: R10.

- [x] T7 — Implementar la logica de guardado de configuracion en
  `AdminConfig.svelte`:
  - "Guardar Configuracion" envia PUT /api/config con el JSON completo.
  - "Guardar Session Timeout" envia PUT /api/setup/session.
  - "Guardar Scale Timeout" envia PUT /api/setup/scale.
  - Cada boton tiene su propio estado de submitting y mensaje de resultado.
  - En exito: toast "Configuracion guardada exitosamente".
  - En error HTTP 422: muestra el mensaje de error del backend.
  - En error de red: muestra mensaje generico + boton reintentar.
  Cubre: R9, R11.

---

## Fase 5 — CRUD de Usuarios (/admin/usuarios)

- [x] T8 — Crear `frontend/src/components/AdminUsers.svelte`:
  - Al montar, carga lista de usuarios via `GET /api/users`.
  - Tabla con columnas: ID, Usuario, Nombre Completo, Documento, Rol,
    Activo (SI/NO), Creado, Actualizado, Acciones.
  - Boton "Nuevo Usuario" sobre la tabla.
  - Por cada fila: botones "Editar" y "Desactivar".
  - Mensaje "No hay usuarios registrados" si lista vacia.
  - Indicador de carga inicial. Mensaje de error con reintento si falla.
  Cubre: R13.

- [x] T9 — Crear `frontend/src/components/UserFormModal.svelte`:
  - Props: `show`, `mode` ("create"|"edit"), `user` (solo edit), `onClose`, `onSave`.
  - Modo create: campos Usuario, Contrasena, Nombre Completo, Documento, Rol.
  - Modo edit: campos Nombre Completo, Documento, Rol, Activo (checkbox),
    Nueva Contrasena (opcional).
  - Validacion frontend: campos requeridos no vacios.
  - Botones "Guardar" / "Cancelar". Cierre via X o overlay click.
  Cubre: R14, R16.

- [x] T10 — Implementar logica de creacion de usuario en `AdminUsers.svelte`:
  - Al guardar en modal create: enviar `POST /api/users`.
  - HTTP 201: cerrar modal, recargar tabla, mostrar "Usuario creado exitosamente".
  - HTTP 409: mostrar error en modal sin cerrar.
  - HTTP 4xx: mostrar error en modal.
  Cubre: R15.

- [x] T11 — Implementar logica de edicion de usuario en `AdminUsers.svelte`:
  - Al hacer clic en "Editar": abrir modal con datos del usuario pre-poblados.
  - Al guardar: enviar `PUT /api/users/{id}`.
  - HTTP 200: cerrar modal, recargar tabla, mostrar mensaje de exito.
  - HTTP 404: mostrar "Usuario no encontrado".
  Cubre: R17.

- [x] T12 — Implementar logica de desactivacion de usuario en `AdminUsers.svelte`:
  - Al hacer clic en "Desactivar": mostrar `ConfirmModal` con
    "Esta seguro de desactivar al usuario X?".
  - Si confirma: enviar `DELETE /api/users/{id}`.
  - HTTP 200: recargar tabla, mostrar "Usuario desactivado exitosamente".
  - Si cancela: no hacer nada.
  Cubre: R18.

- [x] T13 — Implementar recarga automatica de tabla tras operaciones CRUD
  en `AdminUsers.svelte`. Cubre: R36.

- [x] T14 — Implementar manejo de error de red en `AdminUsers.svelte`:
  mostrar "Error de conexion" + boton "Reintentar" si fetch falla.
  Cubre: R37.

---

## Fase 6 — CRUD de Haciendas (/admin/haciendas)

- [x] T15 — Crear `frontend/src/components/AdminHaciendas.svelte`:
  - Al montar, carga lista de haciendas activas via
    `GET /api/haciendas?page=1&page_size=100&sort_by=nombre&sort_order=asc`.
  - Tabla con columnas: ID, Codigo, Nombre, Creado, Actualizado, Acciones.
  - Boton "Nueva Hacienda" sobre la tabla.
  - Por cada fila: botones "Editar" y "Eliminar".
  - Mensaje "No hay haciendas registradas" si lista vacia.
  - Indicador de carga inicial. Mensaje de error con reintento si falla.
  Cubre: R19.

- [x] T16 — Crear `frontend/src/components/HaciendaFormModal.svelte`:
  - Props: `show`, `mode` ("create"|"edit"), `hacienda` (solo edit),
    `onClose`, `onSave`.
  - Campos: Codigo (text, max 8 chars), Nombre (text, max 255 chars).
  - Validacion frontend: campos requeridos no vacios, Codigo max 8 chars,
    Nombre max 255 chars.
  Cubre: R20, R22.

- [x] T17 — Implementar logica de creacion de hacienda en `AdminHaciendas.svelte`:
  - Al guardar en modal create: enviar `POST /api/haciendas`.
  - HTTP 201: cerrar modal, recargar tabla, mostrar exito.
  - HTTP 409: mostrar error en modal sin cerrar.
  Cubre: R21.

- [x] T18 — Implementar logica de edicion de hacienda en `AdminHaciendas.svelte`:
  - Al guardar en modal edit: enviar `PUT /api/haciendas/{id}`.
  - HTTP 200: cerrar modal, recargar tabla, mostrar exito.
  - HTTP 409/404: mostrar error en modal.
  Cubre: R22.

- [x] T19 — Implementar logica de eliminacion (soft-delete) de hacienda
  en `AdminHaciendas.svelte`:
  - Al hacer clic en "Eliminar": mostrar ConfirmModal con
    "Esta seguro de eliminar la hacienda X? (eliminacion logica)".
  - Si confirma: enviar `DELETE /api/haciendas/{id}`.
  - HTTP 200: recargar tabla, mostrar "Hacienda eliminada exitosamente".
  - HTTP 404: mostrar "Hacienda no encontrada".
  Cubre: R23, R39.

- [x] T20 — Implementar recarga automatica tras CRUD en `AdminHaciendas.svelte`.
  Cubre: R36.

- [x] T21 — Implementar manejo de error de red en `AdminHaciendas.svelte`.
  Cubre: R37.

---

## Fase 7 — CRUD de Suertes (/admin/suertes)

- [x] T22 — Crear `frontend/src/components/AdminSuertes.svelte`:
  - Dropdown de seleccion de Hacienda en la parte superior (cargado via
    `GET /api/haciendas?page=1&page_size=100`).
  - Mensaje inicial "Seleccione una hacienda para ver sus suertes"
    mientras no hay hacienda seleccionada.
  - Al seleccionar una hacienda, carga suertes via
    `GET /api/suertes?hacienda_id=X`.
  - Tabla con columnas: ID, Hacienda ID, Codigo Suerte, Creado,
    Actualizado, Acciones.
  - Boton "Nueva Suerte" sobre la tabla.
  - Por cada fila: botones "Editar" y "Eliminar".
  - Mensaje "No hay suertes registradas para esta hacienda" si lista vacia.
  Cubre: R24, R25.

- [x] T23 — Crear `frontend/src/components/SuerteFormModal.svelte`:
  - Props: `show`, `mode`, `suerte` (solo edit), `haciendaId` (readonly en create),
    `onClose`, `onSave`.
  - Campos: Hacienda (select, solo en create, deshabilitado), Codigo Suerte
    (text, max 4 chars).
  - Validacion: Codigo Suerte requerido, max 4 chars.
  Cubre: R26, R28.

- [x] T24 — Implementar logica de creacion de suerte en `AdminSuertes.svelte`:
  - Al guardar: enviar `POST /api/suertes` con `{hacienda_id, codigo_suerte}`.
  - HTTP 201: cerrar modal, recargar tabla, mostrar exito.
  - HTTP 409: mostrar error "Codigo de suerte ya existe en esta hacienda".
  Cubre: R27.

- [x] T25 — Implementar logica de edicion de suerte en `AdminSuertes.svelte`:
  - Al guardar en modal edit: enviar `PUT /api/suertes/{id}`.
  - HTTP 200: cerrar modal, recargar tabla, mostrar exito.
  Cubre: R28.

- [x] T26 — Implementar logica de eliminacion de suerte en `AdminSuertes.svelte`:
  - Al hacer clic en "Eliminar": mostrar ConfirmModal.
  - Si confirma: enviar `DELETE /api/suertes/{id}`.
  - HTTP 200: recargar tabla, mostrar "Suerte eliminada exitosamente".
  Cubre: R29, R39.

- [x] T27 — Implementar recarga automatica tras CRUD en `AdminSuertes.svelte`.
  Cubre: R36.

- [x] T28 — Implementar manejo de error de red en `AdminSuertes.svelte`.
  Cubre: R37.

---

## Fase 8 — Panel de Backups (/admin/backup)

- [x] T29 — Crear `frontend/src/components/AdminBackup.svelte`:
  - Al montar, carga historial via `GET /api/backup/status`.
  - Tabla con columnas: ID, Archivo, Tamano (bytes), Checksum Local,
    Copia USB (SI/NO), Checksum USB, Error, Fecha.
  - Mensaje "No hay registros de backup" si lista vacia.
  - Indicador de carga inicial. Mensaje de error con reintento si falla.
  - Boton "Refrescar" que recarga la tabla.
  - Boton "Ejecutar Backup" que envia `POST /api/backup/run`.
  Cubre: R30, R33.

- [x] T30 — Implementar logica de ejecucion de backup en `AdminBackup.svelte`:
  - Al hacer clic en "Ejecutar Backup": enviar `POST /api/backup/run`.
  - HTTP 202: mostrar "Backup iniciado en segundo plano",
    deshabilitar boton por 30 segundos con texto "Procesando..." + spinner.
  - HTTP 4xx/5xx: mostrar mensaje de error, NO deshabilitar boton.
  - Error de red: mostrar mensaje generico + boton reintentar.
  Cubre: R31, R32.

- [x] T31 — Implementar boton "Refrescar" en `AdminBackup.svelte` que
  recarga la tabla via `GET /api/backup/status`. Cubre: R33.

---

## Fase 9 — Integracion, build y verificacion

- [x] T32 — Verificar que el sidebar de navegacion funciona en todas las
  rutas `/admin/*` y que la seccion activa se resalta correctamente.
  Cubre: R34.

- [x] T33 — Verificar que la navegacion directa por URL (hash) a cada
  sub-ruta admin funciona correctamente sin pasar por el dashboard.
  Cubre: R38.

- [x] T34 — Verificar que el interceptor 401 del `api.js` redirige al login
  cuando el token expira en cualquier vista admin. Cubre: R41.

- [x] T35 — Ejecutar `npm run build` en `frontend/` y verificar que no hay
  errores de compilacion. Cubre: verificacion Nivel 1.

- [x] T36 — Copiar `frontend/dist/*` a `src/static/` y verificar que los
  archivos esten en la ubicacion correcta. Cubre: verificacion.

- [x] T37 — Ejecutar `./init.ps1` — todos los bloques `[OK]`.
  Cubre: verificacion Nivel 3.

- [x] T38 — Verificar trazabilidad completa en `progress/impl_frontend_admin.md`:
  mapear cada `R<n>` a su test o verificacion manual. Cubre: trazabilidad.
