# Requirements — Modo Manual de Emergencia

> Feature 9 — emergency_mode  
> EARS notation: Ubicuo, Evento, Estado, Opcional, No deseado  
> Covers: RF-020a through RF-020k  
> Dependencies: features 2 (auth_rbac), 3 (user_management), 7 (sms_service)

---

## R1 — Modal de solicitud (RF-020a)

El sistema DEBE exponer un modal de solicitud de modo manual accesible desde la
sesión del analista en el kiosco, con campos para seleccionar un supervisor y
especificar un motivo.

---

## R2 — Lista de administradores en modal (RF-020a)

El modal de solicitud DEBE mostrar una lista de usuarios con rol `admin` y
estado `is_active = true` disponibles para autorizar, obtenida del endpoint
`GET /api/emergency/admins`.

---

## R3 — Campo motivo obligatorio (RF-020a)

El modal de solicitud DEBE incluir un campo de texto para el motivo de la
solicitud. CUANDO el analista envía la solicitud sin especificar motivo, el
sistema DEBE rechazar el envío y mostrar un mensaje de error indicando que el
motivo es obligatorio.

---

## R4 — Envío de SMS al administrador (RF-020b)

CUANDO el analista envía una solicitud de modo manual desde el kiosco, el
sistema DEBE enviar un SMS al número de teléfono del administrador seleccionado
que contenga:
- Nombre o ID del analista que solicita
- Motivo de la solicitud
- Instrucciones para autorizar (comandos SMS disponibles)

Cubre: RF-020b

---

## R5 — Múltiples solicitudes simultáneas (RF-020i)

El sistema DEBE permitir múltiples solicitudes simultáneas a distintos
administradores. CUANDO llega la primera respuesta `manual on` (de cualquier
administrador notificado), el sistema DEBE activar el modo manual con esa
autorización y DEBE registrar las demás respuestas como `cancelled` (ya no
aplican).

Cubre: RF-020i

---

## R6 — Activación por SMS: duración por defecto (RF-020c)

CUANDO el sistema recibe un SMS entrante cuyo texto coincide exactamente con
`"manual on"` (case-insensitive, sin espacios adicionales), el sistema DEBE
activar el modo manual con una duración de 24 horas (1440 minutos) desde el
momento de recepción.

Cubre: RF-020c

---

## R7 — Activación por SMS: duración específica (RF-020c)

CUANDO el sistema recibe un SMS entrante cuyo texto coincide con el patrón
`"manual on Xh"` o `"manual on Xm"` (case-insensitive, donde X es un entero
positivo), el sistema DEBE activar el modo manual por el período especificado:
- `Xh`: duración de X horas
- `Xm`: duración de X minutos

Cubre: RF-020c

---

## R8 — Extensión por SMS (RF-020f)

CUANDO el sistema recibe un SMS entrante cuyo texto coincide con el patrón
`"manual on EXT Xh"` o `"manual on EXT Xm"` (case-insensitive) Y el modo
manual está actualmente activo, el sistema DEBE extender el tiempo restante
sumando el período especificado al `expires_at` actual.

Cubre: RF-020f

---

## R9 — Suspensión por SMS (RF-020g)

CUANDO el sistema recibe un SMS entrante cuyo texto coincide exactamente con
`"manual off"` (case-insensitive) Y el modo manual está actualmente activo,
el sistema DEBE desactivar el modo manual inmediatamente y registrar el evento
como `cancelled`.

Cubre: RF-020g

---

## R10 — Desactivación automática por vencimiento (RF-020h)

CUANDO la fecha/hora actual alcanza o supera el valor de `expires_at`
registrado para el modo manual activo, el sistema DEBE desactivar el modo
manual automáticamente y bloquear la edición manual del campo de peso en el
formulario de captura.

Cubre: RF-020h

---

## R11 — Activación directa por SMS sin solicitud previa (RF-020d)

El administrador (supervisor) DEBE poder activar el modo manual directamente
enviando un SMS `"manual on [duración]"` desde su número de teléfono
registrado, sin necesidad de que exista una solicitud previa desde el kiosco.

Cubre: RF-020d

---

## R12 — Reinicio del temporizador (caso borde)

SI el modo manual ya está activo Y llega un nuevo comando `"manual on"` o
`"manual on Xh/Xm"` (case-insensitive) desde un número de administrador,
ENTONCES el sistema DEBE reiniciar el temporizador con la nueva duración
especificada (o 24h por defecto), sobreescribiendo el valor anterior de
`expires_at`.

---

## R13 — Edición del campo de peso en modo manual (RF-020e)

MIENTRAS el modo manual está activo (el estado retornado por
`GET /api/emergency/status` indica `active: true`), el frontend DEBE permitir
al operador editar manualmente los campos de peso en el formulario de captura,
sin requerir lectura desde la báscula.

Cubre: RF-020e

---

## R14 — Persistencia del estado ante cortes de energía (RF-020k)

CUANDO el sistema se inicia (lifespan de FastAPI), el sistema DEBE restaurar
el estado del modo manual desde la base de datos: debe buscar el registro más
reciente en `emergency_mode_log` con `status = 'active'` y, si existe y
`expires_at` es posterior a la hora actual, reactivar el modo manual con el
`expires_at` recuperado. Si `expires_at` ya expiró, debe marcar el registro
como `expired` sin reactivar el modo.

Cubre: RF-020k

---

## R15 — Registro de auditoría en emergency_mode_log (RF-020j)

Cada solicitud, autorización, activación, extensión, suspensión, expiración y
comando inválido DEBE quedar registrada en la tabla `emergency_mode_log` con
timestamp, datos completos del evento y origen del comando (sms / ui).

Cubre: RF-020j

---

## R16 — Comando SMS inválido

SI el sistema recibe un SMS entrante cuyo texto no coincide con ningún comando
válido (`manual on`, `manual on Xh/Xm`, `manual on EXT Xh/Xm`, `manual off`)
ENTONCES el sistema DEBE:
- Ignorar el comando y no modificar el estado del modo manual.
- Registrar el evento en `emergency_mode_log` con `status = 'invalid'` y el texto crudo recibido.
- Responder al remitente con un SMS que indique que el comando no es válido y
  muestre la lista de comandos aceptados: `manual on`, `manual on Xh/Xm`,
  `manual on EXT Xh/Xm`, `manual off`.

---

## R17 — Verificación del emisor del SMS

CUANDO el sistema recibe un comando SMS de tipo `manual on`, `manual on EXT X`
o `manual off`, DEBE verificar que el número de teléfono emisor corresponda a
un usuario con rol `admin` registrado en la tabla `users`. SI el emisor no es
un administrador, el sistema DEBE:
- Ignorar el comando.
- Registrarlo como no autorizado en `emergency_mode_log`.
- Responder al remitente con un SMS informando que los comandos de modo manual
  sólo se aceptan desde números de teléfono registrados de administradores.

---

## R18 — Notificación al solicitante

CUANDO se activa el modo manual (ya sea por respuesta SMS a una solicitud o
por activación directa), el sistema DEBE registrar el evento en la bitácora.
SI la activación corresponde a una solicitud previa, el sistema DEBE actualizar
el registro de solicitud original vinculándolo al registro de activación mediante
`request_id`.

---

## R19 — Extensión denegada si modo inactivo

SI el modo manual no está activo Y el sistema recibe un comando `manual on EXT
Xh/Xm`, ENTONCES el sistema DEBE:
- Ignorar el comando y registrarlo como `invalid` en `emergency_mode_log`.
- Responder al remitente con un SMS informando que el modo manual no está
  activo y que el comando correcto para activarlo es `manual on` o
  `manual on Xh/Xm`.

---
