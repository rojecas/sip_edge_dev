# Requirements — Servicio de Notificaciones y Reportes SMS

> Feature 7 — sms_service  
> EARS notation: Ubicuo, Evento, Estado, Opcional, No deseado

---

## R1 — Envío de SMS (dual dev/prod)

CUANDO el SMSService recibe una solicitud de envío con un número de teléfono
no vacío y un mensaje no vacío, el sistema DEBE enviar el SMS al número
indicado a través del módem GSM gestionado por ModemManager (producción) o
simulando el envío mediante log (desarrollo).

Cubre: RF-012

---

## R2 — Alerta por 3+ intentos fallidos de login

CUANDO un usuario acumula 3 o más intentos fallidos de inicio de sesión
consecutivos, el sistema DEBE enviar un SMS de alerta a todos los números
configurados en `sms.admin_phones` informando del evento.

Cubre: RF-014

---

## R3 — Contador de intentos fallidos por usuario

El sistema DEBE mantener un contador `failed_login_attempts` por usuario que
se incrementa en 1 en cada intento de inicio de sesión fallido y se resetea a
0 en cada inicio de sesión exitoso.

Cubre: RF-014

---

## R4 — Reseteo del contador tras alerta

CUANDO se envía una alerta por 3 o más intentos fallidos consecutivos, el
sistema DEBE resetear el contador `failed_login_attempts` a 0 para el usuario
que generó la alerta, evitando alertas repetidas sin nuevos intentos.

Cubre: RF-014

---

## R5 — Reporte programado de turno

CUANDO la hora del sistema (HH:MM) coincide con alguno de los horarios
configurados en `sms.scheduled_reports`, el sistema DEBE enviar un SMS con un
resumen de las operaciones del turno a todos los números configurados en
`sms.admin_phones`.

Cubre: RF-013

---

## R6 — Configuración de horarios de reporte

Los horarios de reporte DEBEN ser configurables en el archivo `config.yaml`
bajo la clave `sms.scheduled_reports`, con valores por defecto
`["06:00", "14:00", "22:00"]`.

Cubre: RF-013

---

## R7 — Configuración de números de administrador

La lista de números de administrador DEBE ser configurable en el archivo
`config.yaml` bajo la clave `sms.admin_phones`, pudiendo estar vacía (si está
vacía, no se envían alertas ni reportes por SMS).

Cubre: RF-012

---

## R8 — Tolerancia a fallos en envío de SMS

SI el envío de un SMS falla (error de mmcli, módem no disponible, tiempo de
espera agotado) ENTONCES el sistema DEBE registrar el error en el log con
nivel `ERROR` y continuar la ejecución sin interrumpir el servicio ni abortar
el envío de otros SMS en la misma ronda.

Cubre: RF-012

---

## R9 — Modo desarrollo (simulación sin módem)

CUANDO la variable de entorno `DEV_MODE` está establecida como `true` (o `1` o
`yes`), el SMSService DEBE simular el envío de SMS registrando en log con
nivel `INFO` el mensaje y el destinatario, sin ejecutar `mmcli` ni requerir
módem GSM.

Cubre: RF-012

---

## R10 — Carga de configuración SMS al iniciar

CUANDO el sistema se inicia, DEBE cargar la configuración de la sección `sms`
del archivo `config.yaml` e inicializar el planificador de reportes
periódicos. Si la sección `sms` no existe en `config.yaml`, DEBE usar los
valores por defecto (admin_phones vacío, horarios `["06:00","14:00","22:00"]`).

Cubre: RF-012, RF-013

---

## R11 — Contenido del reporte de turno

CUANDO se envía un reporte de turno programado, el sistema DEBE incluir en el
cuerpo del SMS el período del turno, el número total de pesajes realizados en
ese período y la suma de pesos registrados.

Cubre: RF-013

---

## R12 — Prevención de envíos duplicados de reporte

MIENTRAS el planificador esté activo, el sistema DEBE asegurar que no se
envíe más de un reporte por el mismo horario en el mismo día, evitando
duplicados si el servicio se reinicia o si el planificador se ejecuta varias
veces en el mismo minuto.

Cubre: RF-013
