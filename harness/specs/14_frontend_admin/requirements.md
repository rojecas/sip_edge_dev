# Requirements — Frontend: Panel de Administracion

> Feature 14. Acceptance: RF-F14-01 a RF-F14-07. EARS notation.

---

## R1
CUANDO un usuario autenticado con rol "admin" navega a `/admin`, el sistema
DEBE mostrar un dashboard con cards de acceso rapido a cada seccion
administrativa: Configuracion, Usuarios, Haciendas, Suertes, y Backup. Cada
card DEBE contener un titulo, un icono, y un enlace que navega a la ruta
correspondiente. Cubre: RF-F14-01.

## R2
CUANDO el admin hace clic en la card "Configuracion" del dashboard, el sistema
DEBE navegar a `/admin/config`. Cubre: RF-F14-01, RF-F14-02.

## R3
CUANDO el admin hace clic en la card "Usuarios" del dashboard, el sistema
DEBE navegar a `/admin/usuarios`. Cubre: RF-F14-01, RF-F14-04.

## R4
CUANDO el admin hace clic en la card "Haciendas" del dashboard, el sistema
DEBE navegar a `/admin/haciendas`. Cubre: RF-F14-01, RF-F14-05.

## R5
CUANDO el admin hace clic en la card "Suertes" del dashboard, el sistema
DEBE navegar a `/admin/suertes`. Cubre: RF-F14-01, RF-F14-06.

## R6
CUANDO el admin hace clic en la card "Backup" del dashboard, el sistema
DEBE navegar a `/admin/backup`. Cubre: RF-F14-01, RF-F14-07.

## R7
CUANDO el admin navega a `/admin/config`, el sistema DEBE mostrar un
formulario con las siguientes secciones agrupadas:

- **RS485**: campos "Path" (texto), "Baudrate" (select con valores: 300, 600,
  1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200), "Paridad" (select con
  valores: N, E, O, M, S), "Data Bits" (select con valores: 5, 6, 7, 8),
  "Stop Bits" (select con valores: 1.0, 1.5, 2.0), y un boton "Test RS485"
  que llama `POST /api/config/test/rs485`.
- **RS232**: los mismos campos que RS485, con boton "Test RS232" que llama
  `POST /api/config/test/rs232`.
- **GSM**: campo "Modem Index" (numerico), y boton "Test GSM" que llama
  `POST /api/config/test/gsm`.

Cubre: RF-F14-02.

## R8
CUANDO el admin navega a `/admin/config`, el sistema DEBE cargar la
configuracion actual del sistema via `GET /api/config` y pre-poblar todos
los campos del formulario con los valores obtenidos. MIENTRAS la carga esta
en progreso, DEBE mostrar un indicador de carga. SI la carga falla, DEBE
mostrar un mensaje de error. Cubre: RF-F14-02.

## R9
CUANDO el admin modifica cualquier campo de configuracion y hace clic en un
boton "Guardar configuracion", el sistema DEBE enviar `PUT /api/config` con
el JSON completo de `{rs485: {...}, rs232: {...}, gsm: {...}}`. SI la
respuesta es 200 ENTONCES el sistema DEBE mostrar un mensaje "Configuracion
guardada exitosamente". SI la respuesta es 422 ENTONCES el sistema DEBE
mostrar el mensaje de error del servidor SIN perder los cambios del
formulario. Cubre: RF-F14-02.

## R10
CUANDO el admin hace clic en "Test RS485", "Test RS232" o "Test GSM", el
sistema DEBE enviar `POST /api/config/test/{port}` con el nombre del puerto
correspondiente. MIENTRAS la prueba se ejecuta, el boton DEBE mostrar un
indicador de carga y DEBE estar deshabilitado. SI la respuesta contiene
`"status": "ok"` ENTONCES el sistema DEBE mostrar un mensaje "Prueba exitosa"
en color verde junto al boton. SI la respuesta contiene `"status": "fail"`
ENTONCES el sistema DEBE mostrar el mensaje de error en color rojo junto al
boton. Cubre: RF-F14-02.

## R11
CUANDO el admin navega a `/admin/config`, el sistema DEBE mostrar los
siguientes campos de configuracion adicionales debajo de las secciones de
puertos:

- "Session Timeout (minutos)": campo numerico, valor por defecto 15. Al hacer
  clic en "Guardar Session Timeout", el sistema DEBE enviar
  `PUT /api/setup/session` con `{session_timeout_minutes: <valor>}`.
- "Scale Timeout (segundos)": campo numerico entre 1 y 10, valor por defecto
  3. Al hacer clic en "Guardar Scale Timeout", el sistema DEBE enviar
  `PUT /api/setup/scale` con `{timeout_seconds: <valor>}`.

SI la respuesta de cualquiera de los dos PUT es 200 ENTONCES el sistema DEBE
mostrar un mensaje de exito. SI la respuesta es 422 ENTONCES el sistema DEBE
mostrar el mensaje de error. Cubre: RF-F14-03.

## R12
CUANDO el admin navega a `/admin/config`, el sistema DEBE cargar los valores
actuales de session timeout y scale timeout desde `GET /api/config` y
pre-poblar los campos correspondientes. Cubre: RF-F14-03.

## R13
CUANDO el admin navega a `/admin/usuarios`, el sistema DEBE cargar la lista
completa de usuarios via `GET /api/users` y mostrarlos en una tabla con las
columnas: ID, Usuario, Nombre Completo, Documento, Rol, Activo, Creado,
Actualizado. SI la lista esta vacia, DEBE mostrar el mensaje "No hay usuarios
registrados". MIENTRAS carga, DEBE mostrar un indicador de carga. SI la
carga falla, DEBE mostrar un mensaje de error. Cubre: RF-F14-04.

## R14
CUANDO el admin esta en `/admin/usuarios` y hace clic en un boton "Nuevo
Usuario", el sistema DEBE abrir un modal con campos: "Usuario" (texto),
"Contrasena" (password), "Nombre Completo" (texto), "Documento" (texto,
opcional), "Rol" (select: admin, operator, corresponsal). El modal DEBE
tener botones "Guardar" y "Cancelar". Cubre: RF-F14-04.

## R15
CUANDO el admin completa el formulario de nuevo usuario y hace clic en
"Guardar", el sistema DEBE enviar `POST /api/users` con los datos del
formulario. SI la respuesta es 201 ENTONCES el sistema DEBE cerrar el modal,
recargar la tabla de usuarios y mostrar un mensaje "Usuario creado
exitosamente". SI la respuesta es 409 (usuario duplicado) ENTONCES el sistema
DEBE mostrar el mensaje de error en el modal SIN cerrarlo. Cubre: RF-F14-04.

## R16
CUANDO el admin esta en `/admin/usuarios` y hace clic en el icono/boton
"Editar" junto a un usuario, el sistema DEBE abrir un modal con los campos
pre-poblados: "Nombre Completo", "Documento", "Rol", "Activo" (checkbox), y
"Nueva Contrasena" (password, opcional). Cubre: RF-F14-04.

## R17
CUANDO el admin modifica los campos en el modal de edicion y hace clic en
"Guardar Cambios", el sistema DEBE enviar `PUT /api/users/{id}` con los
datos modificados. SI la respuesta es 200 ENTONCES el sistema DEBE cerrar el
modal, recargar la tabla y mostrar un mensaje de exito. SI la respuesta es
404 ENTONCES el sistema DEBE mostrar "Usuario no encontrado". Cubre: RF-F14-04.

## R18
CUANDO el admin esta en `/admin/usuarios` y hace clic en el icono/boton
"Desactivar" junto a un usuario activo, el sistema DEBE mostrar un modal de
confirmacion "Esta seguro de desactivar al usuario X?". SI el admin confirma
ENTONCES el sistema DEBE enviar `DELETE /api/users/{id}`. SI la respuesta es
200 ENTONCES el sistema DEBE recargar la tabla y mostrar "Usuario desactivado
exitosamente". SI el admin cancela ENTONCES el sistema NO DEBE realizar
ninguna accion. Cubre: RF-F14-04.

## R19
CUANDO el admin navega a `/admin/haciendas`, el sistema DEBE cargar la lista
de haciendas activas via `GET /api/haciendas?page=1&page_size=100&sort_by=nombre&sort_order=asc`
y mostrarlas en una tabla con las columnas: ID, Codigo, Nombre, Creado,
Actualizado, Acciones. SI la lista esta vacia, DEBE mostrar "No hay haciendas
registradas". MIENTRAS carga, DEBE mostrar un indicador de carga. Cubre:
RF-F14-05.

## R20
CUANDO el admin esta en `/admin/haciendas` y hace clic en "Nueva Hacienda",
el sistema DEBE abrir un modal con campos: "Codigo" (texto, maximo 8
caracteres), "Nombre" (texto, maximo 255 caracteres). Cubre: RF-F14-05.

## R21
CUANDO el admin completa el formulario de nueva hacienda y hace clic en
"Guardar", el sistema DEBE enviar `POST /api/haciendas` con los datos. SI la
respuesta es 201 ENTONCES el sistema DEBE cerrar el modal, recargar la tabla
y mostrar "Hacienda creada exitosamente". SI la respuesta es 409 (codigo
duplicado) ENTONCES el sistema DEBE mostrar el error en el modal SIN cerrarlo.
Cubre: RF-F14-05.

## R22
CUANDO el admin esta en `/admin/haciendas` y hace clic en "Editar" junto a
una hacienda, el sistema DEBE abrir un modal con los campos "Codigo" y
"Nombre" pre-poblados. Al guardar, DEBE enviar `PUT /api/haciendas/{id}`.
SI la respuesta es 200 ENTONCES el sistema DEBE cerrar el modal, recargar la
tabla y mostrar un mensaje de exito. Cubre: RF-F14-05.

## R23
CUANDO el admin esta en `/admin/haciendas` y hace clic en "Eliminar" junto a
una hacienda, el sistema DEBE mostrar un modal de confirmacion "Esta seguro
de eliminar la hacienda X? (eliminacion logica)". SI el admin confirma
ENTONCES el sistema DEBE enviar `DELETE /api/haciendas/{id}`. SI la respuesta
es 200 ENTONCES el sistema DEBE recargar la tabla y mostrar "Hacienda
eliminada exitosamente". SI la respuesta es 404 ENTONCES el sistema DEBE
mostrar "Hacienda no encontrada". Cubre: RF-F14-05.

## R24
CUANDO el admin navega a `/admin/suertes`, el sistema DEBE mostrar un
dropdown para seleccionar una Hacienda (cargado via `GET /api/haciendas`).
MIENTRAS no se haya seleccionado una hacienda, la tabla de suertes DEBE
mostrar el mensaje "Seleccione una hacienda para ver sus suertes".
Cubre: RF-F14-06.

## R25
CUANDO el admin selecciona una hacienda en el dropdown de `/admin/suertes`,
el sistema DEBE cargar las suertes de esa hacienda via
`GET /api/suertes?hacienda_id=X` y mostrarlas en una tabla con las columnas:
ID, Hacienda ID, Codigo Suerte, Creado, Actualizado, Acciones. SI no hay
suertes para esa hacienda, DEBE mostrar "No hay suertes registradas para
esta hacienda". MIENTRAS carga, DEBE mostrar un indicador de carga.
Cubre: RF-F14-06.

## R26
CUANDO el admin esta en `/admin/suertes` y hace clic en "Nueva Suerte", el
sistema DEBE abrir un modal con campos: "Hacienda" (select, pre-seleccionado
con la hacienda actual), "Codigo Suerte" (texto, maximo 4 caracteres).
Cubre: RF-F14-06.

## R27
CUANDO el admin completa el formulario de nueva suerte y hace clic en
"Guardar", el sistema DEBE enviar `POST /api/suertes` con
`{hacienda_id, codigo_suerte}`. SI la respuesta es 201 ENTONCES el sistema
DEBE cerrar el modal, recargar la tabla de suertes y mostrar "Suerte creada
exitosamente". SI la respuesta es 409 (codigo duplicado en misma hacienda)
ENTONCES el sistema DEBE mostrar el error en el modal SIN cerrarlo.
Cubre: RF-F14-06.

## R28
CUANDO el admin esta en `/admin/suertes` y hace clic en "Editar" junto a una
suerte, el sistema DEBE abrir un modal con el campo "Codigo Suerte"
pre-poblado. Al guardar, DEBE enviar `PUT /api/suertes/{id}` con
`{codigo_suerte}`. SI la respuesta es 200 ENTONCES el sistema DEBE cerrar el
modal y recargar la tabla. Cubre: RF-F14-06.

## R29
CUANDO el admin esta en `/admin/suertes` y hace clic en "Eliminar" junto a
una suerte, el sistema DEBE mostrar un modal de confirmacion. SI el admin
confirma ENTONCES el sistema DEBE enviar `DELETE /api/suertes/{id}`. SI la
respuesta es 200 ENTONCES el sistema DEBE recargar la tabla y mostrar "Suerte
eliminada exitosamente". Cubre: RF-F14-06.

## R30
CUANDO el admin navega a `/admin/backup`, el sistema DEBE cargar el historial
de los ultimos 10 backups via `GET /api/backup/status` y mostrarlos en una
tabla con las columnas: ID, Archivo, Tamano, Checksum Local, Copia USB,
Checksum USB, Error, Fecha. MIENTRAS carga, DEBE mostrar un indicador de
carga. SI la lista esta vacia, DEBE mostrar "No hay registros de backup".
Cubre: RF-F14-07.

## R31
CUANDO el admin esta en `/admin/backup` y hace clic en el boton "Ejecutar
Backup", el sistema DEBE enviar `POST /api/backup/run`. SI la respuesta es
202 ENTONCES el sistema DEBE mostrar un mensaje "Backup iniciado en segundo
plano" y deshabilitar el boton por 30 segundos para evitar ejecuciones
multiples. MIENTRAS el boton esta deshabilitado, DEBE mostrar "Procesando..."
y un spinner. Cubre: RF-F14-07.

## R32
SI `POST /api/backup/run` devuelve HTTP 4xx o 5xx ENTONCES el sistema DEBE
mostrar un mensaje de error SIN deshabilitar el boton. Cubre: RF-F14-07.

## R33
CUANDO el admin navega a `/admin/backup`, el sistema DEBE mostrar un boton
"Refrescar" que recarga la tabla de backups via `GET /api/backup/status`.
Cubre: RF-F14-07.

## R34
MIENTRAS el admin esta en cualquier vista de administracion
(`/admin`, `/admin/config`, `/admin/usuarios`, `/admin/haciendas`,
`/admin/suertes`, `/admin/backup`), el sistema DEBE mostrar un sidebar o
barra de navegacion lateral con enlaces a todas las secciones administrativas,
permitiendo la navegacion rapida entre secciones sin pasar por el dashboard.
El sidebar DEBE resaltar visualmente la seccion activa. Cubre: RF-F14-01.

## R35
El sistema DEBE validar que solo los usuarios con rol "admin" puedan acceder
a cualquier ruta bajo `/admin/`. SI un usuario con rol "operator" intenta
navegar a `/admin/*`, el sistema DEBE redirigirlo a `/kiosco`. Cubre:
frontend-architecture.md (autorizacion por rol).

## R36
CUANDO el admin completa exitosamente cualquier operacion CRUD (crear,
editar, desactivar/eliminar) en las vistas de usuarios, haciendas o suertes,
el sistema DEBE recargar automaticamente la lista correspondiente para
reflejar los cambios. Cubre: RF-F14-04, RF-F14-05, RF-F14-06.

## R37
CUANDO el admin esta en `/admin/usuarios`, `/admin/haciendas`, o
`/admin/suertes` y ocurre un error de red (fetch falla por conexion), el
sistema DEBE mostrar un mensaje "Error de conexion. Verifique que el servidor
este disponible." con un boton "Reintentar". Cubre: RF-F14-04, RF-F14-05,
RF-F14-06.

## R38
CUANDO el admin navega a cualquier sub-ruta de administracion
(`/admin/config`, `/admin/usuarios`, `/admin/haciendas`, `/admin/suertes`,
`/admin/backup`) directamente por URL (sin pasar por el dashboard), el
sistema DEBE cargar la seccion correspondiente correctamente. Cubre:
RF-F14-02, RF-F14-04, RF-F14-05, RF-F14-06, RF-F14-07.

## R39
CUANDO el admin esta en `/admin/haciendas` o `/admin/suertes` y realiza una
operacion de eliminacion, el sistema NO DEBE eliminar fisicamente el registro
sino marcar su `deleted_at` (soft-delete, manejado por el backend). El
frontend DEBE enviar la peticion DELETE correspondiente y confiar en que el
backend realiza la eliminacion logica. Cubre: RF-F14-05, RF-F14-06.

## R40
CUANDO el admin navega a `/admin/config`, los valores de baudrate, paridad,
data_bits y stop_bits DEBEN mostrarse en selects (dropdown) con valores
predefinidos y NO en campos de texto libre. Los valores permitidos son:

- **Baudrate**: 300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200
- **Parity**: N, E, O, M, S
- **Data Bits**: 5, 6, 7, 8
- **Stop Bits**: 1.0, 1.5, 2.0

Cubre: RF-F14-02, RF-F14-03.

## R41
CUANDO el admin esta en cualquier vista de administracion y la sesion expira
(HTTP 401 del backend), el sistema DEBE redirigir al modal de login con el
mensaje "Sesion expirada o no autorizada". Esto DEBE ser manejado por el
interceptor 401 del `api.js` existente. Cubre: RF-F14-01 a RF-F14-07,
frontend-architecture.md seccion 6.1.
