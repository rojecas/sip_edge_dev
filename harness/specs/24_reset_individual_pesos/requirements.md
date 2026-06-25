# Requirements — Reset Individual de Pesos en Kiosko de Pesaje

> Feature 24 — reset_individual_pesos
> Formato: EARS (Easy Approach to Requirements Syntax)

---

## R1

CUANDO el operador visualiza el formulario de pesaje en `/kiosko`, el sistema DEBE
mostrar un botón "Reset" junto a cada campo de peso (peso_muestra, peso_mineral,
peso_vegetal_extrano).

---

## R2

CUANDO el operador presiona el botón Reset de un campo de peso específico,
el sistema DEBE establecer el valor de ese campo a 0.000 sin modificar ningún
otro campo del formulario (los otros campos de peso, los campos de vehículo
y los campos de procedencia DEBEN permanecer intactos).

---

## R3

El sistema DEBE eliminar el botón "Reset general" del área de acciones primarias
del formulario. El sistema DEBE mantener la funcionalidad de reset completo
(todos los campos) disponible como acción secundaria fuera del flujo principal.

---

## R4

El sistema DEBE modificar el endpoint `POST /api/weighings/reset` para aceptar
un cuerpo JSON opcional con el campo `step`. Los valores válidos para `step`
DEBEN ser `"peso_muestra"`, `"peso_mineral"` y `"peso_vegetal_extrano"`.

---

## R5

CUANDO el backend recibe `POST /api/weighings/reset` con `step` válido,
el sistema DEBE responder con HTTP 200 y un mensaje que confirme el campo
reiniciado (ej. `{"mensaje": "Campo peso_muestra reiniciado"}`).

---

## R6

SI el backend recibe `POST /api/weighings/reset` con `step` inválido o con
un valor no reconocido, ENTONCES el sistema DEBE responder con HTTP 400 y
un mensaje de error que liste los valores aceptados.

---

## R7

CUANDO el backend recibe `POST /api/weighings/reset` sin el campo `step`
(o con cuerpo vacío), el sistema DEBE responder con HTTP 200 preservando
el comportamiento de reset completo actual.

---

## R8

CUANDO un usuario no autenticado intenta `POST /api/weighings/reset`,
el sistema DEBE responder con HTTP 401 independientemente del contenido
del cuerpo de la solicitud.
