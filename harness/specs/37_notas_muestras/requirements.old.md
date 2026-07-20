# Feature 37 — notas_muestras: Campo de Notas Colapsable en Vista de Toma de Muestras

> Requirements en notación EARS estricta.
> Cada R<n> es verificable por al menos un test concreto.
> Auditoría spec-validator 2026-07-20: Spec correcto, sin cambios requeridos.
>   Gaps en design/tasks (no en requirements) corregidos en esos archivos.

---

## R1 — Persistencia: columna notas en weighings
El sistema DEBE incluir una columna `notas` de tipo `TEXT` nullable en la tabla `weighings` de la base de datos.

## R2 — UI: campo colapsable en formulario de pesaje
MIENTRAS el operador visualiza el formulario de pesaje en `/kiosko`, el sistema DEBE mostrar un área de texto colapsable para notas debajo de la sección de pesos, con un control de expandir/colapsar.

## R3 — UI: expandir campo de notas
CUANDO el operador activa el control de expandir del campo de notas, el sistema DEBE mostrar el área de texto completa para ingreso de texto, con altura suficiente para al menos 3 líneas.

## R4 — UI: colapsar campo de notas
CUANDO el operador activa el control de colapsar del campo de notas estando expandido, el sistema DEBE ocultar el área de texto y mostrar solo un indicador del estado actual (texto "Notas" + resumen de primeras palabras si hay contenido).

## R5 — Persistencia al confirmar pesaje
CUANDO el operador confirma el pesaje mediante POST `/api/weighings`, el sistema DEBE persistir el contenido del campo `notas` en la columna `notas` del registro creado en la tabla `weighings`.

## R6 — Reset del campo de notas
CUANDO el operador ejecuta la acción de limpiar formulario (POST `/api/weighings/reset` general), el sistema DEBE reiniciar el campo de notas a valor vacío en el frontend.

## R7 — Visibilidad en el historial de pesajes
CUANDO el operador visualiza el historial de pesajes en `/kiosko/historial`, el sistema DEBE mostrar una columna "Notas" en `HistoryTable` con el texto de notas de cada pesaje.

## R8 — Indicador de notas vacías en historial
SI el pesaje no tiene notas registradas (columna `notas` es `NULL` o cadena vacía), ENTONCES el sistema DEBE mostrar "—" en la columna Notas del historial.

## R9 — Tool SQL get_weighing_notes para consultas SMS
El sistema DEBE exponer una herramienta SQL `get_weighing_notes` en el catálogo `TOOL_DEFINITIONS` del agente AI, que acepte como parámetros `vagon` (string opcional) y/o `fecha_inicio`/`fecha_fin` (strings opcionales en formato YYYY-MM-DD), y devuelva las notas de pesajes que coincidan con los filtros.

## R10 — Consulta de notas vía SMS
CUANDO el agente AI recibe una consulta SMS que solicita notas de pesaje (ej. "notas del vagon V5", "notas de hoy"), el sistema DEBE ejecutar la herramienta `get_weighing_notes` y responder con las notas relevantes vía SMS.

## R11 — Notas nulas en creación de pesaje
CUANDO el operador envía el formulario de pesaje sin contenido en el campo de notas (valor `None`, cadena vacía o campo omitido), el sistema DEBE persistir `NULL` en la columna `notas` del registro en `weighings`.

## R12 — Campo notas en respuesta de API
CUANDO el sistema retorna un registro de pesaje (POST `/api/weighings`, GET `/api/weighings`, GET `/api/weighings/{id}`), el sistema DEBE incluir el campo `notas: str | None` en la respuesta `WeighingResponse`.

## R13 — Sin truncamiento en persistencia
El sistema DEBE aceptar y persistir el texto completo del campo notas sin truncamiento, utilizando el tipo `TEXT` de MySQL/MariaDB (hasta 65.535 bytes).
