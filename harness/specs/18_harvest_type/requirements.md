# Requirements — Campo tipo de cosecha en registro de pesaje

> Feature 18 — harvest_type  
> EARS notation: Ubicuo, Evento, Estado, Opcional, No deseado

---

## R1 — Columna tipo_cosecha en BD

La tabla `weighings` DEBE tener una columna `tipo_cosecha` de tipo ENUM con exactamente 6 valores: `'Manual - Incendio'`, `'Manual - Quemado'`, `'Manual - Verde'`, `'Mecanico - Incendio'`, `'Mecanico - Verde'`, `'No convencional - Verde'`. La columna DEBE ser NOT NULL y tener valor por defecto `'Mecanico - Verde'`.

Cubre: AC 1, AC 2

---

## R2 — Migración de base de datos

CUANDO se ejecuta la migración de base de datos, el sistema DEBE añadir la columna `tipo_cosecha` a la tabla `weighings` existente mediante un `ALTER TABLE` con las características definidas en R1.

Cubre: AC 1, AC 2

---

## R3 — Modelo ORM Weighing

El modelo ORM `Weighing` en `src/models.py` DEBE incluir el campo `tipo_cosecha` como columna SQLAlchemy de tipo Enum con los 6 valores definidos en R1, NOT NULL, default `'Mecanico - Verde'`.

Cubre: AC 1, AC 2

---

## R4 — Schema WeighingCreate acepta tipo_cosecha

El schema Pydantic `WeighingCreate` DEBE incluir el campo `tipo_cosecha` como `str` opcional, con valor por defecto `'Mecanico - Verde'`.

Cubre: AC 4

---

## R5 — Validación de tipo_cosecha inválido

SI `POST /api/weighings` recibe un valor de `tipo_cosecha` que NO está entre los 6 valores permitidos, ENTONCES el sistema DEBE devolver HTTP 422 con un mensaje de error descriptivo.

Cubre: AC 4

---

## R6 — Default en creación de pesaje

CUANDO `POST /api/weighings` se ejecuta sin incluir el campo `tipo_cosecha`, el sistema DEBE asignar el valor por defecto `'Mecanico - Verde'` al registro persistido.

Cubre: AC 2, AC 4

---

## R7 — Schema WeighingResponse incluye tipo_cosecha

El schema Pydantic `WeighingResponse` DEBE incluir el campo `tipo_cosecha` como `str`, expuesto en todas las respuestas de endpoints de pesaje (`GET /api/weighings`, `GET /api/weighings/{id}`, `POST /api/weighings`).

Cubre: AC 4, AC 6

---

## R8 — Select de tipo de cosecha en formulario de kiosco

CUANDO un operador autenticado accede al formulario de pesaje en `/kiosco`, el sistema DEBE mostrar un elemento `<select>` con las 6 opciones de tipo de cosecha, etiquetado como "Tipo de Cosecha". El valor por defecto seleccionado DEBE ser `'Mecanico - Verde'`.

Cubre: AC 3

---

## R9 — Persistencia del tipo de cosecha al confirmar

CUANDO el operador selecciona un tipo de cosecha en el formulario y hace clic en "Confirmar Pesaje", el sistema DEBE incluir el valor de `tipo_cosecha` en el body de `POST /api/weighings` y persistirlo en la columna `tipo_cosecha` de la tabla `weighings`.

Cubre: AC 4

---

## R10 — Filtro tipo_cosecha en GET /api/anomalies

CUANDO un usuario con rol admin hace `GET /api/anomalies` con el query parameter opcional `?tipo_cosecha=X`, el sistema DEBE ejecutar la detección de anomalías considerando únicamente los pesajes cuyo `tipo_cosecha` coincida exactamente con el valor proporcionado.

Cubre: AC 5

---

## R11 — Columna tipo_cosecha en historial de pesajes

CUANDO un usuario autenticado navega a `/kiosco/historial`, el sistema DEBE mostrar la columna "Tipo Cosecha" en la tabla del historial, con el valor de `tipo_cosecha` de cada registro.

Cubre: AC 6
