# Feature 17 — Frontend Analytics: Reportes, Anomalías y Consola IA

> Requirements en notación EARS estricta.

---

## R1
CUANDO un administrador navega a `/admin/reportes`, el sistema DEBE cargar la lista de plantillas de reportes via `GET /api/reports/templates` y mostrarlas en una tabla con columnas ID, Nombre, Schedule, Métricas, Estado y Acciones.

## R2
CUANDO la carga de plantillas desde `GET /api/reports/templates` falla por error de red o servidor, el sistema DEBE mostrar un mensaje de error descriptivo y un botón "Reintentar".

## R3
CUANDO no hay plantillas de reportes registradas, el sistema DEBE mostrar un mensaje informativo "No hay plantillas de reportes" con un icono ilustrativo.

## R4
CUANDO un administrador hace clic en "Nueva Plantilla", el sistema DEBE mostrar un modal con campos: nombre (texto), schedule (lista de horarios HH:MM seleccionables), recipients (teléfonos SMS), metrics (checkboxes de métricas disponibles) e is_active (toggle).

## R5
CUANDO un administrador guarda una plantilla (creación o edición), el sistema DEBE validar que el nombre no esté vacío, enviar la petición a `POST /api/reports/templates` (crear) o `PUT /api/reports/templates/{id}` (editar), cerrar el modal y recargar la tabla.

## R6
CUANDO un administrador hace clic en "Eliminar" sobre una plantilla, el sistema DEBE mostrar un modal de confirmación; SI confirma ENTONCES el sistema DEBE enviar `DELETE /api/reports/templates/{id}` y recargar la tabla.

## R7
CUANDO un administrador navega a `/admin/anomalias`, el sistema DEBE cargar el historial de anomalías via `GET /api/anomalies/history` con soporte de paginación y mostrar los resultados en una tabla paginada con columnas ID, Capa, Z-Score, Valor Métrica, Umbral, Reporte LLM, Enviado SMS y Fecha.

## R8
SI la paginación del historial de anomalías tiene más de una página, el sistema DEBE mostrar controles de paginación (Anterior/Siguiente, selector de page size, indicador página N de M).

## R9
CUANDO un administrador navega a `/admin/agente`, el sistema DEBE mostrar una interfaz tipo chat con un área de mensajes (scrollable) y un campo de texto para escribir consultas.

## R10
CUANDO un administrador envía una consulta en la interfaz de agente, el sistema DEBE enviar `POST /api/agent/query` con el texto, mostrar la consulta en el historial del chat y luego mostrar la respuesta del agente.

## R11
MIENTRAS el agente está procesando una consulta, el sistema DEBE mostrar un indicador de carga (ej. "Pensando...") y DESHABILITAR el campo de texto y botón de envío.

## R12
CUANDO la consulta al agente falla (error de red o servidor 503), el sistema DEBE mostrar un mensaje de error en el chat y permitir reintentar.

## R13
CUANDO un administrador hace clic en "Detectar Ahora", el sistema DEBE mostrar un panel con parámetros configurables: window_size (slider/input numérico, default 120), z_threshold (slider/input float, default 3.0), y tipo_cosecha (select opcional).

## R14
CUANDO un administrador ejecuta la detección con los parámetros configurados, el sistema DEBE llamar a `GET /api/anomalies` con los parámetros elegidos y mostrar los resultados en una tabla.

## R15
SI la detección bajo demanda no encuentra anomalías, el sistema DEBE mostrar "No se detectaron anomalías con los parámetros seleccionados".

## R16
CUANDO un administrador navega a cualquier ruta `/admin/reportes`, `/admin/anomalias` o `/admin/agente` sin sesión activa, el sistema DEBE redirigir al login mostrando "Sesión expirada o no autorizada" (aplica el interceptor 401 existente).

## R17
EL sistema DEBE incluir enlaces de navegación en el sidebar del panel admin para las secciones Reportes, Anomalías y Agente, con iconos distintivos.

## R18
EL sistema DEBE incluir en el Dashboard admin cards de acceso rápido para Reportes, Anomalías y Agente con descripciones funcionales.

## R19
CUANDO un administrador guarda una plantilla de reporte, el sistema DEBE almacenar los destinatarios como referencias a usuarios (user_id) en una tabla pivote eport_template_users, NO como texto plano de numeros de telefono en la columna ecipients.

## R20
CUANDO el sistema envia un reporte programado, DEBE resolver los numeros de telefono de los destinatarios mediante JOIN desde la tabla users a traves de la tabla pivote eport_template_users, garantizando que los telefonos esten siempre actualizados.
