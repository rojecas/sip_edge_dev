# Requirements — Frontend: Login, Kiosco de Pesaje y Logout

> Feature 13. Acceptance: RF-F13-01 a RF-F13-10 + requisitos derivados de
> frontend-architecture.md secciones 3.1 y 6.1. EARS notation.

---

## R1
CUANDO el SPA se carga en Chromium modo kiosco (`http://localhost:8000`),
SI no existe un JWT valido en `localStorage` ENTONCES el sistema DEBE mostrar
un modal de login con campos "Usuario" y "Contrasena" y un boton "Iniciar
Sesion", SIN navegar a una pagina de login separada. Cubre: RF-F13-01.

## R2
CUANDO el SPA se carga y existe un JWT valido en `localStorage`, el sistema
DEBE decodificar el rol del token y redirigir automaticamente a `/kiosco`
si el rol es "operator" o a `/admin` si el rol es "admin". Cubre: RF-F13-01,
RF-F13-02.

## R3
CUANDO el usuario hace clic en "Iniciar Sesion", el sistema DEBE enviar
`POST /api/auth/login` con `{username, password}`. SI la respuesta es 200
ENTONCES el sistema DEBE almacenar el `access_token` y el `role` en
`localStorage` y redirigir segun el rol (`/kiosco` para operator, `/admin`
para admin). Cubre: RF-F13-02.

## R4
SI `POST /api/auth/login` devuelve HTTP 401 o 403 ENTONCES el sistema DEBE
mostrar un mensaje de error en el modal de login ("Usuario o contrasena
incorrectos") SIN redirigir. Cubre: RF-F13-01.

## R5
CUANDO el usuario hace clic en "Olvido su contrasena", el sistema DEBE abrir
un modal con campos "Usuario" y "PIN (4 digitos)" y un boton "Verificar PIN".
El modal DEBE cerrarse al hacer clic en la X o en el overlay. Cubre: RF-F13-10.

## R6
CUANDO el usuario ingresa usuario + PIN de 4 digitos y hace clic en
"Verificar PIN", el sistema DEBE enviar `POST /api/auth/verify-reset-pin`
con `{username, pin}`. SI la respuesta es 200 ENTONCES el sistema DEBE abrir
un segundo modal para ingresar la nueva contrasena (campos: "Nueva contrasena",
"Confirmar contrasena"). Cubre: RF-F13-10.

## R7
CUANDO el usuario ingresa su nueva contrasena y confirmacion y hace clic en
"Cambiar Contrasena", el sistema DEBE enviar `POST /api/auth/complete-reset`
con `{reset_token, new_password, confirm_password}`. SI la respuesta es 200
ENTONCES el sistema DEBE mostrar un mensaje de exito y cerrar el modal tras
2 segundos, dejando visible el modal de login. Cubre: RF-F13-10.

## R8
SI `POST /api/auth/verify-reset-pin` devuelve HTTP 4xx ENTONCES el sistema
DEBE mostrar un mensaje de error ("PIN invalido o expirado") en el modal
sin cerrarlo. Cubre: RF-F13-10.

## R9
SI `POST /api/auth/complete-reset` devuelve HTTP 4xx ENTONCES el sistema
DEBE mostrar un mensaje de error en el modal de cambio de contrasena.
Cubre: RF-F13-10.

## R10
El boton "Cerrar sesion" DEBE estar siempre visible en la esquina superior
derecha de TODAS las vistas del SPA (/kiosco, /kiosco/historial, /admin, etc.).
Cubre: RF-F13-03.

## R11
CUANDO el usuario hace clic en "Cerrar sesion", el sistema DEBE mostrar un
modal de confirmacion "Esta seguro de cerrar sesion?". SI el usuario confirma
ENTONCES el sistema DEBE eliminar el JWT y el rol de `localStorage` y mostrar
el modal de login. SI el usuario cancela ENTONCES el sistema NO DEBE cerrar
la sesion. Cubre: RF-F13-03.

## R12
MIENTRAS el usuario esta autenticado, el sistema DEBE verificar en cada
navegacion que el JWT no haya expirado comparando el `iat` (issued at) del
token con el tiempo transcurrido y el `session_timeout_minutes` configurado.
SI el JWT esta expirado ENTONCES el sistema DEBE eliminar el token de
`localStorage`, redirigir al modal de login y mostrar el mensaje "Sesion
expirada". Cubre: frontend-architecture.md seccion 3.1.

## R13
CUANDO cualquier peticion HTTP del SPA devuelve HTTP 401, el sistema DEBE
interceptar la respuesta, eliminar el JWT de `localStorage`, redirigir al
modal de login y mostrar un mensaje "Sesion expirada o no autorizada".
Cubre: frontend-architecture.md seccion 6.1.

## R14
CUANDO el usuario autenticado con rol "operator" navega a `/kiosco`, el
sistema DEBE mostrar el formulario de pesaje con los siguientes campos:
- "Tractomula" (texto)
- "Vagon" (texto)
- "Guia" (texto)
- Dropdown "Hacienda" (cargado via `GET /api/haciendas`)
- Dropdown "Suerte" (cargado via `GET /api/suertes?hacienda_id=X`
  dinamicamente al seleccionar una hacienda)
- "Peso Muestra" (numerico, con botones "Tara" y "Leer")
- "Peso Mineral" (numerico, con botones "Tara" y "Leer")
- "Peso Vegetal" (numerico, con botones "Tara" y "Leer")
Cubre: RF-F13-04.

## R15
CUANDO el operador hace clic en "Leer" junto a un campo de peso, el sistema
DEBE tomar el valor actual del peso en vivo del WebSocket y asignarlo a ese
campo. Cubre: RF-F13-04, RF-F13-05.

## R16
CUANDO el operador hace clic en "Tara" junto a un campo de peso, el sistema
DEBE enviar el comando de tara a la bascula via API correspondiente y poner
el campo de peso en cero. Cubre: RF-F13-04.

## R17
MIENTRAS el operador esta en la vista `/kiosco`, el sistema DEBE mantener
una conexion WebSocket a `/ws/scale?token=<jwt>` y mostrar el peso en vivo
en un indicador destacado, incluyendo el estado de estabilidad (`is_stable`).
CUANDO `is_stable` es `true` el sistema DEBE mostrar un indicador verde
("Estable"). CUANDO `is_stable` es `false` el sistema DEBE mostrar un
indicador amarillo ("Inestable"). Cubre: RF-F13-05.

## R18
SI la conexion WebSocket `/ws/scale` se cierra inesperadamente, el sistema
DEBE reintentar la conexion cada 2 segundos hasta un maximo de 5 intentos.
SI todos los reintentos fallan ENTONCES el sistema DEBE mostrar un mensaje
"Bascula desconectada" en el indicador de peso. Cubre: RF-F13-05.

## R19
CUANDO el operador hace clic en "Confirmar" en el formulario de pesaje, el
sistema DEBE validar que todos los campos requeridos esten completos
(tractomula, vagon, guia, hacienda, suerte, 3 pesos) y enviar
`POST /api/weighings` con los datos del formulario. SI la respuesta es 201
ENTONCES el sistema DEBE mostrar un mensaje de exito "Pesaje registrado" y
limpiar el formulario. Cubre: RF-F13-06.

## R20
SI `POST /api/weighings` devuelve HTTP 4xx o 5xx ENTONCES el sistema DEBE
mostrar un mensaje de error detallado SIN limpiar el formulario.
Cubre: RF-F13-06.

## R21
CUANDO el operador hace clic en "Reset", el sistema DEBE mostrar un modal
de confirmacion "Esta seguro de limpiar el formulario?". SI el operador
confirma ENTONCES el sistema DEBE enviar `POST /api/weighings/reset` y
limpiar todos los campos del formulario. SI el operador cancela ENTONCES
el sistema NO DEBE modificar el formulario. Cubre: RF-F13-06.

## R22
CUANDO un operador autenticado navega a `/kiosco/historial`, el sistema
DEBE cargar los pesajes del operador actual via `GET /api/weighings` con
los parametros `?page=1&page_size=20&sort_by=fecha&sort_order=desc` y
mostrarlos en una tabla paginada con columnas: ID, Fecha, Hora, Tractomula,
Vagon, Guia, Hacienda, Suerte, Peso Muestra, Peso Mineral, Peso Vegetal.
Cubre: RF-F13-07.

## R23
MIENTRAS el operador esta en la vista `/kiosco` o `/kiosco/historial`, el
sistema DEBE consultar `GET /api/emergency/status` cada 5 segundos (polling).
Cubre: RF-F13-08.

## R24
SI `GET /api/emergency/status` devuelve `manual_mode: true`, el sistema DEBE
mostrar un banner de emergencia en la parte superior de la pantalla con el
mensaje "MODO MANUAL ACTIVO - Pesos editables" y el tiempo restante.
MIENTRAS el modo manual esta activo, los campos de peso (muestra, mineral,
vegetal) DEBEN ser editables manualmente (input type="number" habilitado).
Cubre: RF-F13-08.

## R25
SI `GET /api/emergency/status` devuelve `manual_mode: false`, el sistema
DEBE asegurarse de que los campos de peso NO sean editables manualmente
(solo se actualizan via los botones Tara/Leer o WebSocket). El banner de
emergencia NO DEBE mostrarse. Cubre: RF-F13-08.

## R26
CUANDO el operador hace clic en un boton "Solicitar emergencia" (visible
en el banner o en el formulario), el sistema DEBE abrir un modal que:
- Cargue la lista de supervisores disponibles via `GET /api/emergency/admins`
- Muestre un dropdown para seleccionar un supervisor
- Muestre un campo de texto para el motivo (obligatorio)
- Tenga un boton "Enviar solicitud"
Cubre: RF-F13-09.

## R27
CUANDO el operador selecciona un supervisor, ingresa un motivo y hace clic
en "Enviar solicitud", el sistema DEBE enviar `POST /api/emergency/request`
con `{admin_id, reason}`. SI la respuesta es 200 ENTONCES el sistema DEBE
mostrar un mensaje "Solicitud enviada. Espere respuesta del supervisor."
y cerrar el modal. Cubre: RF-F13-09.

## R28
SI `POST /api/emergency/request` devuelve HTTP 4xx o 5xx ENTONCES el sistema
DEBE mostrar un mensaje de error en el modal SIN cerrarlo.
Cubre: RF-F13-09.

## R29
MIENTRAS el sistema realiza peticiones HTTP (fetch), el sistema DEBE anadir
el header `Authorization: Bearer <token>` automaticamente a todas las
solicitudes a la API, tomando el token de `localStorage`.
Cubre: frontend-architecture.md seccion 6.1.

## R30
SI el modal de login esta visible y el usuario presiona Enter en el campo
de contrasena, el sistema DEBE ejecutar la accion de "Iniciar Sesion".
Cubre: RF-F13-01.

## R31
El sistema DEBE mostrar el nombre de usuario del operador autenticado en la
esquina superior izquierda de las vistas `/kiosco` y `/kiosco/historial`,
junto con el rol. Cubre: frontend-architecture.md seccion 3.1.

## R32
CUANDO el operador selecciona una Hacienda en el dropdown, el sistema DEBE
cargar las Suertes correspondientes via `GET /api/suertes?hacienda_id=X` de
forma asincrona y actualizar el dropdown de Suertes. MIENTRAS carga, el
dropdown DEBE mostrar "Cargando...". SI no hay suertes disponibles, el
dropdown DEBE mostrar "Sin suertes disponibles". Cubre: RF-F13-04.

## R33
El sistema DEBE proporcionar un mecanismo para que la vista `/admin`
redirija correctamente a los usuarios con rol admin cuando el JWT esta
presente, funcionando como placeholder ya que su contenido completo se
desarrolla en la Feature 14. Cubre: RF-F13-02.

## R34
CUANDO el usuario cierra sesion o el JWT expira, el sistema DEBE limpiar
todos los datos de sesion en `localStorage` (token, rol) y recargar el
SPA mostrando unicamente el modal de login. Cubre: RF-F13-03.

## R35
CUANDO el SPA recibe datos del WebSocket `/ws/scale`, el sistema DEBE
actualizar el indicador de peso en vivo en tiempo real SIN recargar la
pagina y SIN requerir interaccion del usuario. Cubre: RF-F13-05.

## R36
El sistema DEBE desplegarse como archivos estaticos servidos por FastAPI
desde `src/static/`. El backend DEBE servir `index.html` en la ruta raiz `/`
y en cualquier ruta que no coincida con `/api/`, `/ws/`, `/login` o
`/health`. Cubre: frontend-architecture.md seccion 7.1.

## R37
CUANDO el operador esta en `/kiosco/historial`, la tabla de historial DEBE
mostrar los registros ordenados por fecha descendente (mas reciente primero).
El sistema DEBE mostrar controles de paginacion (numero de pagina actual,
total de paginas, botones "Anterior" y "Siguiente"). SI la lista esta vacia,
DEBE mostrar el mensaje "No hay pesajes registrados". Cubre: RF-F13-07.

## R38
CUANDO el operador esta en `/kiosco/historial`, el sistema DEBE mostrar
controles de filtro por rango de fechas: campo "Fecha desde" y campo
"Fecha hasta" (input type="date"). CUANDO el operador selecciona un rango
de fechas, el sistema DEBE enviar `GET /api/weighings` con los parametros
adicionales `&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`. Cubre: RF-F13-07.

## R39
CUANDO el sistema realiza cualquier peticion `GET /api/weighings`, DEBE
enviar los parametros de paginacion `page` (numero de pagina, default 1)
y `page_size` (registros por pagina, default 20, maximo 100). El sistema
DEBE interpretar la respuesta paginada del backend que incluye:
`{ "items": [...], "total": N, "page": P, "page_size": S, "total_pages": T }`.
Cubre: RF-F13-07.

## R40
CUANDO el sistema carga el dropdown de Haciendas via `GET /api/haciendas`,
DEBE enviar los parametros `?page=1&page_size=100&sort_by=nombre&sort_order=asc`.
El sistema DEBE cargar todas las paginas necesarias para poblar el dropdown
completo, o alternativamente implementar busqueda/busqueda incremental
mientras el usuario escribe. Cubre: RF-F13-04, frontend-architecture.md.

## R41
SI el token JWT almacenado en `localStorage` no tiene formato valido o no
contiene `iat` (issued at) al cargar el SPA, el sistema DEBE tratar al
usuario como no autenticado y mostrar el modal de login. Cubre: RF-F13-01,
frontend-architecture.md seccion 3.1.

## R42
El modal de login NO DEBE permitir el envio del formulario si los campos
"Usuario" o "Contrasena" estan vacios. El boton "Iniciar Sesion" DEBE estar
deshabilitado mientras los campos requeridos esten vacios. Cubre: RF-F13-01.
