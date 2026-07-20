# Requirements — Feature 38: Operator Hacienda/Suerte CRUD

## R1 — Pestañas de navegación
CUANDO un operador autenticado navega a la ruta `/kiosco`, el sistema DEBE mostrar 4 pestañas en la barra de navegación: **Pesaje** (ruta `/kiosco`), **Historial** (ruta `/kiosco/historial`), **Haciendas** (ruta `/kiosco/haciendas`) y **Suertes** (ruta `/kiosco/suertes`).

## R2 — Gestión completa de Haciendas
CUANDO un operador selecciona la pestaña "Haciendas", el sistema DEBE mostrar la misma vista de gestión de haciendas que tiene el administrador en `/admin/haciendas`: tabla paginada con columnas Código y Nombre, botón "Nueva Hacienda" que abre el modal de creación, botón de edición por fila, y botón de eliminación (soft-delete) con confirmación.

## R3 — Gestión completa de Suertes
CUANDO un operador selecciona la pestaña "Suertes", el sistema DEBE mostrar la misma vista de gestión de suertes que tiene el administrador en `/admin/suertes`: dropdown de hacienda para filtrar, tabla paginada con columnas Hacienda y Código Suerte, botón "Nueva Suerte" que abre el modal de creación, botón de edición por fila, y botón de eliminación con confirmación.

## R4 — POST /api/haciendas permite operator
CUANDO el backend recibe `POST /api/haciendas` con un token JWT que contiene el rol `"operator"`, el sistema DEBE procesar la creación y devolver 201 en lugar de 403.

## R5 — PUT /api/haciendas/{id} permite operator
CUANDO el backend recibe `PUT /api/haciendas/{id}` con un token JWT que contiene el rol `"operator"`, el sistema DEBE procesar la actualización y devolver 200 en lugar de 403.

## R6 — DELETE /api/haciendas/{id} permite operator
CUANDO el backend recibe `DELETE /api/haciendas/{id}` con un token JWT que contiene el rol `"operator"`, el sistema DEBE ejecutar el soft-delete y devolver 204 en lugar de 403.

## R7 — POST /api/suertes permite operator
CUANDO el backend recibe `POST /api/suertes` con un token JWT que contiene el rol `"operator"`, el sistema DEBE procesar la creación y devolver 201 en lugar de 403.

## R8 — PUT /api/suertes/{id} permite operator
CUANDO el backend recibe `PUT /api/suertes/{id}` con un token JWT que contiene el rol `"operator"`, el sistema DEBE procesar la actualización y devolver 200 en lugar de 403.

## R9 — DELETE /api/suertes/{id} permite operator
CUANDO el backend recibe `DELETE /api/suertes/{id}` con un token JWT que contiene el rol `"operator"`, el sistema DEBE ejecutar la eliminación y devolver 204 en lugar de 403.

## R10 — Disponibilidad inmediata para pesaje
CUANDO un operador crea o edita una hacienda o suerte desde el kiosko, el sistema DEBE asegurar que los cambios estén disponibles en el formulario de pesaje (F36) al navegar de regreso, sin requerir recarga completa de la aplicación.

## R11 — Corresponsales sin acceso
CUANDO un usuario con rol `"corresponsal"` intenta acceder a cualquier ruta `/kiosco/*`, el sistema NO DEBE permitir el acceso (los corresponsales no tienen login ni JWT, por diseño de F2).

## R12 — Errores de duplicado
CUANDO un operador intenta crear una hacienda con código duplicado o una suerte con código duplicado en la misma hacienda, el sistema DEBE devolver HTTP 409 con el mensaje de error correspondiente y el frontend DEBE mostrar el error sin cerrar el formulario.
