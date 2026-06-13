# Requirements — system_config

> Feature: Configuración del Sistema y Persistencia
> RFs: RF-015, RF-016, RF-017
> Stack: Python 3.11 + FastAPI + HTMX + MariaDB

---

## R1 — Mostrar formulario de configuración

CUANDO el Administrador accede a la vista de configuración (`/admin/config`),
el sistema DEBE mostrar un formulario HTML con todos los parámetros de hardware
editables y sus valores actuales cargados desde `config.yaml`.

---

## R2 — Configurar puerto RS485 (báscula)

El sistema DEBE permitir al Administrador configurar los siguientes parámetros
del puerto RS485 de la báscula:

- Ruta del dispositivo (ej. `/dev/ttyUSB0`)
- Baudrate (9600, 19200, 38400, 57600, 115200)
- Paridad (None, Even, Odd)
- Bytes de datos (7, 8)
- Bits de parada (1, 2)

---

### R3 — Configurar puerto del módem GSM

El sistema DEBE permitir al Administrador configurar los siguientes parámetros
del puerto serial del módem GSM:

- Ruta del dispositivo (ej. `/dev/ttyUSB2`)
- Baudrate (9600, 19200, 38400, 57600, 115200)
- Timeout de respuesta (500–5000 ms, default 3000)

---

### R3.2 — Configurar puerto RS232 (PC externo)

El sistema DEBE permitir al Administrador configurar los siguientes parámetros
del puerto RS232 para transmisión a PC externo:

- Ruta del dispositivo (ej. `/dev/ttyS0`)
- Baudrate (9600, 19200, 38400, 57600, 115200)
- Data bits (7, 8)
- Stop bits (1, 2)
- Paridad (None, Even, Odd)
- Timeout de envío (500–5000 ms, default 2000)

---

## R4 — Probar conectividad de báscula (RS485)

CUANDO el Administrador presiona el botón "Test Báscula", el sistema DEBE:

1. Abrir el puerto serial configurado con los parámetros actuales.
2. Enviar un comando de prueba predefinido.
3. Esperar respuesta hasta el timeout configurado.
4. Mostrar en pantalla el resultado: "OK — Respuesta: <data>" o "ERROR — <mensaje>".

SI el puerto no existe o no responde, ENTONCES el sistema DEBE mostrar un
mensaje de error descriptivo (no un stack trace).

---

## R5 — Probar conectividad del módem GSM

CUANDO el Administrador presiona el botón "Test GSM", el sistema DEBE:

1. Abrir el puerto serial configurado para el módem.
2. Enviar comando `AT\r\n`.
3. Esperar respuesta `OK` hasta el timeout configurado.
4. Mostrar en pantalla "OK — Módem responde" o "ERROR — Sin respuesta del módem".

---

## R5.2 — Probar conectividad del puerto RS232

CUANDO el Administrador presiona el botón "Test RS232", el sistema DEBE:

1. Abrir el puerto serial configurado para RS232.
2. Enviar un comando de prueba predefinido (loopback o eco si está conectado).
3. Verificar que el puerto está disponible y configurable.
4. Mostrar en pantalla "OK — Puerto RS232 disponible" o "ERROR — <mensaje>".

SI el puerto no existe o está en uso, ENTONCES el sistema DEBE mostrar un
mensaje de error descriptivo.

---

## R6 — Guardar configuración con validación

CUANDO el Administrador envía el formulario de configuración, el sistema DEBE:

1. Validar que todos los campos requeridos tengan valores válidos.
2. SI la validación falla, ENTONCES devolver el formulario con errores por campo
   (sin recargar la página completa, vía HTMX partial).
3. SI la validación es exitosa, ENTONCES escribir atómicamente `config.yaml`
   (primero en archivo temporal, luego `os.replace()`) y mostrar mensaje
   "Configuración guardada".

---

## R7 — Cargar configuración al iniciar

CUANDO el proceso del backend inicia, el sistema DEBE:

1. Leer `config.yaml` del directorio de trabajo.
2. SI el archivo no existe, ENTONCES crearlo con valores por defecto.
3. Cargar los valores en un singleton de configuración accesible por todos
   los módulos.
4. Aplicar la configuración inmediatamente (sin requerir reinicio adicional).

---

## R8 — Sincronizar reloj del sistema al iniciar

CUANDO el backend inicia, el sistema DEBE verificar que el reloj del sistema
esté sincronizado. SI hay conectividad con servidores NTP, el sistema DEBE
sincronizar la hora mediante `timedatectl set-ntp true`.

MIENTRAS el modo offline está activo (sin conectividad externa), el sistema
NO DEBE intentar sincronización por red y DEBE registrar un aviso en logs.

---

## R9 — Configurar horarios de reportes programados

El sistema DEBE permitir al Administrador configurar los horarios de envío
de reportes SMS programados (por defecto: 06:00, 14:00, 22:00). Cada horario
DEBE ser una hora válida en formato HH:MM.

---

## R10 — Configurar destinatarios de SMS

El sistema DEBE permitir al Administrador gestionar una lista de números
telefónicos autorizados para recibir reportes y alertas SMS. Cada número
DEBE validarse con formato internacional (+XX...).

---

## R11 — Persistencia de configuración ante reinicio

SI el sistema se reinicia (por apagón, mantenimiento o crash), ENTONCES
la configuración DEBE cargarse automáticamente desde `config.yaml` sin
intervención manual. No se requiere reconfigurar tras cada reinicio.

---

## R12 — Protección de acceso

CUANDO un usuario sin rol Admin intenta acceder a `/admin/config`, el sistema
DEBE devolver HTTP 403 y mostrar un mensaje de acceso denegado.

---

## Traceability Matrix

| RF     | Requirements              |
|--------|---------------------------|
| RF-015 | R1, R2, R3, R3.2, R9, R10 |
| RF-016 | R4, R5, R5.2              |
| RF-017 | R6, R7, R8, R11           |
| RF-002 | R12                       |
