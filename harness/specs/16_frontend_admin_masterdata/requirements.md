# Requirements — Frontend Admin: CRUD de Datos Maestros

> Feature 16 (14c) — CRUD de Usuarios, Haciendas y Suertes. EARS notation.
> Corresponde a la subdivisión 14c de la feature 14 original (R13-R29, R36, R37, R39).

---

## R1
CUANDO el admin navega a `/admin/usuarios`, el sistema DEBE cargar la lista
completa de usuarios via `GET /api/users` y mostrarlos en una tabla con las
columnas: ID, Usuario, Nombre Completo, Documento, Rol, Activo, Creado,
Actualizado. SI la lista esta vacia, DEBE mostrar el mensaje "No hay usuarios
registrados". MIENTRAS carga, DEBE mostrar un indicador de carga. SI la
carga falla, DEBE mostrar un mensaje de error. Cubre: RF-F14-03a.

## R2
CUANDO el admin esta en `/admin/usuarios` y hace clic en un boton "Nuevo
Usuario", el sistema DEBE abrir un modal con campos: "Usuario" (texto),
"Contrasena" (password), "Nombre Completo" (texto), "Documento" (texto,
opcional), "Rol" (select: admin, operator, corresponsal). El modal DEBE
tener botones "Guardar" y "Cancelar". Cubre: RF-F14-03b.

## R3
CUANDO el admin completa el formulario de nuevo usuario y hace clic en
"Guardar", el sistema DEBE enviar `POST /api/users` con los datos del
formulario. SI la respuesta es 201 ENTONCES el sistema DEBE cerrar el modal,
recargar la tabla de usuarios y mostrar un mensaje "Usuario creado
exitosamente". SI la respuesta es 409 (usuario duplicado) ENTONCES el sistema
DEBE mostrar el mensaje de error en el modal SIN cerrarlo. Cubre: RF-F14-03b.

## R4
CUANDO el admin esta en `/admin/usuarios` y hace clic en el icono/boton
"Editar" junto a un usuario, el sistema DEBE abrir un modal con los campos
pre-poblados: "Nombre Completo", "Documento", "Rol", "Activo" (checkbox), y
"Nueva Contrasena" (password, opcional). Cubre: RF-F14-03c.

## R5
CUANDO el admin modifica los campos en el modal de edicion y hace clic en
"Guardar Cambios", el sistema DEBE enviar `PUT /api/users/{id}` con los
datos modificados. SI la respuesta es 200 ENTONCES el sistema DEBE cerrar el
modal, recargar la tabla y mostrar un mensaje de exito. SI la respuesta es
404 ENTONCES el sistema DEBE mostrar "Usuario no encontrado". Cubre: RF-F14-03c.

## R6
CUANDO el admin esta en `/admin/usuarios` y hace clic en el icono/boton
"Desactivar" junto a un usuario activo, el sistema DEBE mostrar un modal de
confirmacion "Esta seguro de desactivar al usuario X?". SI el admin confirma
ENTONCES el sistema DEBE enviar `DELETE /api/users/{id}`. SI la respuesta es
200 ENTONCES el sistema DEBE recargar la tabla y mostrar "Usuario desactivado
exitosamente". SI el admin cancela ENTONCES el sistema NO DEBE realizar
ninguna accion. Cubre: RF-F14-03d.

## R7
CUANDO el admin navega a `/admin/haciendas`, el sistema DEBE cargar la lista
de haciendas activas via `GET /api/haciendas?page=1&page_size=100&sort_by=nombre&sort_order=asc`
y mostrarlas en una tabla con las columnas: ID, Codigo, Nombre, Creado,
Actualizado, Acciones. SI la lista esta vacia, DEBE mostrar "No hay haciendas
registradas". MIENTRAS carga, DEBE mostrar un indicador de carga. Cubre: RF-F14-03e.

## R8
CUANDO el admin esta en `/admin/haciendas` y hace clic en "Nueva Hacienda",
el sistema DEBE abrir un modal con campos: "Codigo" (texto, maximo 8
caracteres), "Nombre" (texto, maximo 255 caracteres). Cubre: RF-F14-03e.

## R9
CUANDO el admin completa el formulario de nueva hacienda y hace clic en
"Guardar", el sistema DEBE enviar `POST /api/haciendas` con los datos. SI la
respuesta es 201 ENTONCES el sistema DEBE cerrar el modal, recargar la tabla
y mostrar "Hacienda creada exitosamente". SI la respuesta es 409 (codigo
duplicado) ENTONCES el sistema DEBE mostrar el error en el modal SIN cerrarlo.
Cubre: RF-F14-03f.

## R10
CUANDO el admin esta en `/admin/haciendas` y hace clic en "Editar" junto a
una hacienda, el sistema DEBE abrir un modal con los campos "Codigo" y
"Nombre" pre-poblados. Al guardar, DEBE enviar `PUT /api/haciendas/{id}`.
SI la respuesta es 200 ENTONCES el sistema DEBE cerrar el modal, recargar la
tabla y mostrar un mensaje de exito. Cubre: RF-F14-03f.

## R11
CUANDO el admin esta en `/admin/haciendas` y hace clic en "Eliminar" junto a
una hacienda, el sistema DEBE mostrar un modal de confirmacion "Esta seguro
de eliminar la hacienda X? (eliminacion logica)". SI el admin confirma
ENTONCES el sistema DEBE enviar `DELETE /api/haciendas/{id}`. SI la respuesta
es 200 ENTONCES el sistema DEBE recargar la tabla y mostrar "Hacienda
eliminada exitosamente". SI la respuesta es 404 ENTONCES el sistema DEBE
mostrar "Hacienda no encontrada". Cubre: RF-F14-03f.

## R12
CUANDO el admin navega a `/admin/suertes`, el sistema DEBE mostrar un
dropdown para seleccionar una Hacienda (cargado via `GET /api/haciendas`).
MIENTRAS no se haya seleccionado una hacienda, la tabla de suertes DEBE
mostrar el mensaje "Seleccione una hacienda para ver sus suertes".
Cubre: RF-F14-03g.

## R13
CUANDO el admin selecciona una hacienda en el dropdown de `/admin/suertes`,
el sistema DEBE cargar las suertes de esa hacienda via
`GET /api/suertes?hacienda_id=X` y mostrarlas en una tabla con las columnas:
ID, Hacienda ID, Codigo Suerte, Creado, Actualizado, Acciones. SI no hay
suertes para esa hacienda, DEBE mostrar "No hay suertes registradas para
esta hacienda". MIENTRAS carga, DEBE mostrar un indicador de carga.
Cubre: RF-F14-03g.

## R14
CUANDO el admin esta en `/admin/suertes` y hace clic en "Nueva Suerte", el
sistema DEBE abrir un modal con campos: "Hacienda" (select, pre-seleccionado
con la hacienda actual), "Codigo Suerte" (texto, maximo 4 caracteres).
Cubre: RF-F14-03h.

## R15
CUANDO el admin completa el formulario de nueva suerte y hace clic en
"Guardar", el sistema DEBE enviar `POST /api/suertes` con
`{hacienda_id, codigo_suerte}`. SI la respuesta es 201 ENTONCES el sistema
DEBE cerrar el modal, recargar la tabla de suertes y mostrar "Suerte creada
exitosamente". SI la respuesta es 409 (codigo duplicado en misma hacienda)
ENTONCES el sistema DEBE mostrar el error en el modal SIN cerrarlo.
Cubre: RF-F14-03h.

## R16
CUANDO el admin esta en `/admin/suertes` y hace clic en "Editar" junto a una
suerte, el sistema DEBE abrir un modal con el campo "Codigo Suerte"
pre-poblado. Al guardar, DEBE enviar `PUT /api/suertes/{id}` con
`{codigo_suerte}`. SI la respuesta es 200 ENTONCES el sistema DEBE cerrar el
modal y recargar la tabla. Cubre: RF-F14-03h.

## R17
CUANDO el admin esta en `/admin/suertes` y hace clic en "Eliminar" junto a
una suerte, el sistema DEBE mostrar un modal de confirmacion. SI el admin
confirma ENTONCES el sistema DEBE enviar `DELETE /api/suertes/{id}`. SI la
respuesta es 200 ENTONCES el sistema DEBE recargar la tabla y mostrar "Suerte
eliminada exitosamente". Cubre: RF-F14-03h.

## R18
CUANDO el admin completa exitosamente cualquier operacion CRUD (crear,
editar, desactivar/eliminar) en las vistas de usuarios, haciendas o suertes,
el sistema DEBE recargar automaticamente la lista correspondiente para
reflejar los cambios. Cubre: RF-F14-03i.

## R19
CUANDO el admin esta en `/admin/usuarios`, `/admin/haciendas`, o
`/admin/suertes` y ocurre un error de red (fetch falla por conexion), el
sistema DEBE mostrar un mensaje "Error de conexion. Verifique que el servidor
este disponible." con un boton "Reintentar". Cubre: RF-F14-03j.

## R20
CUANDO el admin esta en `/admin/haciendas` o `/admin/suertes` y realiza una
operacion de eliminacion, el sistema NO DEBE eliminar fisicamente el registro
sino marcar su `deleted_at` (soft-delete, manejado por el backend). El
frontend DEBE enviar la peticion DELETE correspondiente y confiar en que el
backend realiza la eliminacion logica. Cubre: RF-F14-03k.
