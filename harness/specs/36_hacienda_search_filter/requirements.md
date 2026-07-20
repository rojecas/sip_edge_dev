# Requirements — Feature 36: Entrada de Código de Hacienda en Kiosko y AdminSuertes

> Formato: EARS (Easy Approach to Requirements Syntax).
> Cada requirement es verificable por al menos un test concreto.

---

## R1
CUANDO el operador visualiza el formulario de pesaje (`KioskForm`),
el sistema DEBE reemplazar el `<select>` de hacienda por un campo de
entrada de texto donde se teclea el código alfanumérico de la hacienda.

## R2
CUANDO el administrador visualiza la vista `AdminSuertes`,
el sistema DEBE reemplazar el `<select>` de hacienda por un campo de
entrada de texto donde se teclea el código alfanumérico de la hacienda.

## R3
CUANDO el usuario presiona Enter o Tab en el campo de código de hacienda,
el sistema DEBE realizar una única llamada a la API `GET /api/haciendas?search=<codigo>&page_size=1`
para resolver el código. El sistema NO DEBE disparar llamadas por cada keystroke.

## R4
El sistema DEBE exponer un parámetro `search` en `GET /api/haciendas`
que filtre por el campo `codigo` con coincidencia exacta case-insensitive
(ej. `a16` y `A16` resuelven la misma hacienda).

## R5
CUANDO la API retorna una hacienda con el código ingresado,
el sistema DEBE mostrar un display confirmado con el formato único
`CODIGO - NOMBRE` (ej. `131 - Hacienda San José`) tanto en
`KioskForm` como en `AdminSuertes`.

## R6
CUANDO el sistema muestra el display confirmado de una hacienda,
DEBE mostrar junto al mismo un botón de limpiar (icono `x`).

## R7
CUANDO la API no encuentra ninguna hacienda con el código ingresado
(HTTP 200 con `items` vacío), el sistema DEBE mostrar un modal de error
tradicional con:
- Mensaje: "El código 'XXX' no corresponde a ninguna hacienda registrada."
- Explicación: "Esto puede deberse a un error de digitación o a una
  hacienda nueva que aún no ha sido creada."

## R8
CUANDO el modal de error está visible, el sistema DEBE mostrar un botón
**[Reintentar]** que al presionarlo cierra el modal y devuelve el foco
al campo de texto del código.

## R9
CUANDO el modal de error está visible, el sistema DEBE mostrar un botón
**[Crear nueva hacienda]** que al presionarlo navega a la vista
`/kiosco/haciendas` (Feature 38 — creador de haciendas desde el kiosko).

## R10
CUANDO el usuario presiona el botón de limpiar (`x`) en el display
confirmado de la hacienda, el sistema DEBE:
- Eliminar la selección de hacienda.
- Vaciar el dropdown/selector de suertes asociadas.

## R11
El sistema DEBE implementar un componente Svelte compartido
`HaciendaCodeInput.svelte` que encapsule la lógica de entrada, búsqueda
por API, display confirmado, modal de error y limpieza, de forma que
tanto `KioskForm` como `AdminSuertes` lo consuman.
