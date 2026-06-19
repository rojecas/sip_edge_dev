# Tasks — Frontend Admin: CRUD de Datos Maestros

> Marcar `[x]` al completar. Cada task referencia al menos un `R<n>`.
> NOTA: El codigo fuente ya existe del desarrollo de feature 14. Estas tasks
> verifican su correcto funcionamiento y corrigen problemas conocidos.

---

## Fase 1 — Verificacion de CRUD Usuarios (/admin/usuarios)

- [ ] T1 — Verificar que `AdminUsers.svelte` carga lista de usuarios:
  - Llama `GET /api/users` al montar
  - Tabla con columnas: ID, Usuario, Nombre Completo, Documento, Rol, Activo, Creado, Actualizado
  - Mensaje "No hay usuarios registrados" si lista vacia
  - Indicador de carga inicial
  - Mensaje de error con reintento si falla la carga
  Cubre: R1.

- [ ] T2 — Verificar `UserFormModal.svelte` en modo create:
  - Campos: Usuario, Contrasena, Nombre Completo, Documento, Rol
  - Validacion frontend: campos requeridos no vacios
  - Botones "Guardar" y "Cancelar"
  Cubre: R2.

- [ ] T3 — Verificar creacion de usuario:
  - Guardar envia `POST /api/users`
  - HTTP 201 → cierra modal, recarga tabla, muestra exito
  - HTTP 409 → muestra error en modal SIN cerrar
  Cubre: R3.

- [ ] T4 — Verificar `UserFormModal.svelte` en modo edit:
  - Campos pre-poblados: Nombre Completo, Documento, Rol, Activo (checkbox), Nueva Contrasena (opcional)
  Cubre: R4.

- [ ] T5 — Verificar edicion de usuario:
  - Guardar envia `PUT /api/users/{id}`
  - HTTP 200 → cierra modal, recarga tabla, muestra exito
  - HTTP 404 → muestra "Usuario no encontrado"
  Cubre: R5.

- [ ] T6 — Verificar desactivacion de usuario:
  - Clic en "Desactivar" → ConfirmModal con mensaje
  - Confirmar → `DELETE /api/users/{id}`
  - HTTP 200 → recarga tabla, muestra exito
  - Cancelar → no hace nada
  Cubre: R6.

- [ ] T7 — Verificar paginacion en tabla de usuarios (problema conocido):
  - Si hay muchos usuarios, la tabla debe paginar o al menos mostrar los primeros N
  - Considerar agregar paginacion similar a AdminHaciendas
  Cubre: R1.

## Fase 2 — Verificacion de CRUD Haciendas (/admin/haciendas)

- [ ] T8 — Verificar `AdminHaciendas.svelte`:
  - Carga haciendas via `GET /api/haciendas` paginado
  - Tabla: ID, Codigo, Nombre, Creado, Actualizado, Acciones
  - Mensaje "No hay haciendas registradas" si lista vacia
  Cubre: R7.

- [ ] T9 — Verificar `HaciendaFormModal.svelte`:
  - Campos: Codigo (max 8 chars), Nombre (max 255 chars)
  - Validacion frontend: campos requeridos, Codigo max 8, Nombre max 255
  Cubre: R8.

- [ ] T10 — Verificar CRUD operaciones de hacienda:
  - Crear: `POST /api/haciendas`, HTTP 201 cierra modal, 409 muestra error
  - Editar: `PUT /api/haciendas/{id}`, HTTP 200 cierra modal
  - Eliminar: ConfirmModal → `DELETE /api/haciendas/{id}`, HTTP 200 recarga
  Cubre: R9, R10, R11.

## Fase 3 — Verificacion de CRUD Suertes (/admin/suertes)

- [ ] T11 — Verificar `AdminSuertes.svelte`:
  - Dropdown de seleccion de Hacienda arriba
  - Mensaje inicial "Seleccione una hacienda para ver sus suertes"
  - Al seleccionar, carga suertes via `GET /api/suertes?hacienda_id=X`
  - Tabla: ID, Hacienda ID, Codigo Suerte, Creado, Actualizado, Acciones
  Cubre: R12, R13.

- [ ] T12 — Verificar `SuerteFormModal.svelte`:
  - Create: Hacienda (select, readonly), Codigo Suerte (max 4 chars)
  - Edit: Codigo Suerte pre-poblado
  Cubre: R14.

- [ ] T13 — Verificar CRUD operaciones de suerte:
  - Crear: `POST /api/suertes`, HTTP 201 cierra modal, 409 muestra error
  - Editar: `PUT /api/suertes/{id}`, HTTP 200 cierra modal
  - Eliminar: ConfirmModal → `DELETE /api/suertes/{id}`, HTTP 200 recarga
  Cubre: R15, R16, R17.

## Fase 4 — Verificacion transversal

- [ ] T14 — Verificar auto-recarga de tabla tras cada CRUD exitoso:
  - AdminUsers: tras crear, editar, desactivar
  - AdminHaciendas: tras crear, editar, eliminar
  - AdminSuertes: tras crear, editar, eliminar
  Cubre: R18.

- [ ] T15 — Verificar manejo de error de red:
  - Simular desconexion de red en cada CRUD
  - Mostrar "Error de conexion. Verifique que el servidor este disponible."
  - Boton "Reintentar" funcional
  Cubre: R19.

- [ ] T16 — Verificar soft-delete:
  - DELETE en haciendas/suertes llama al endpoint DELETE
  - Frontend no elimina fisicamente, confia en backend
  - Mensaje de confirmacion incluye "(eliminacion logica)"
  Cubre: R20.

## Fase 5 — Build y verificacion

- [ ] T17 — Ejecutar `npm run build` en `frontend/`:
  - Sin errores de compilacion
  Cubre: verificacion Nivel 1.

- [ ] T18 — Copiar `frontend/dist/*` a `src/static/`:
  - Archivos copiados correctamente
  Cubre: verificacion despliegue.

- [ ] T19 — Ejecutar `./init.ps1`:
  - Todos los bloques `[OK]`
  Cubre: verificacion Nivel 3.

- [ ] T20 — Verificar trazabilidad completa en `progress/impl_frontend_admin_masterdata.md`:
  - Mapear cada `R<n>` a su test o verificacion manual
  Cubre: trazabilidad.
