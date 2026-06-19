# Requirements — Frontend Admin: Configuración y Backup

> Feature 15 (14b) — Panel de configuración del sistema y backups. EARS notation.
> Corresponde a la subdivisión 14b de la feature 14 original (R7-R12, R30-R33, R40).

---

## R1
CUANDO el admin navega a `/admin/config`, el sistema DEBE mostrar un
formulario con las siguientes secciones agrupadas:

- **RS485**: campos "Path" (texto), "Baudrate" (select con valores: 300, 600,
  1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200), "Paridad" (select con
  valores: N, E, O, M, S), "Data Bits" (select con valores: 5, 6, 7, 8),
  "Stop Bits" (select con valores: 1.0, 1.5, 2.0), y un boton "Test RS485"
  que llama `POST /api/config/test/rs485`.
- **RS232**: los mismos campos que RS485, con boton "Test RS232" que llama
  `POST /api/config/test/rs232`.
- **GSM**: campo "Modem Index" (numerico), y boton "Test GSM" que llama
  `POST /api/config/test/gsm`.

Cubre: RF-F14-02a.

## R2
CUANDO el admin navega a `/admin/config`, el sistema DEBE cargar la
configuracion actual del sistema via `GET /api/config` y pre-poblar todos
los campos del formulario con los valores obtenidos. MIENTRAS la carga esta
en progreso, DEBE mostrar un indicador de carga. SI la carga falla, DEBE
mostrar un mensaje de error. Cubre: RF-F14-02b.

## R3
CUANDO el admin modifica cualquier campo de configuracion y hace clic en un
boton "Guardar configuracion", el sistema DEBE enviar `PUT /api/config` con
el JSON completo de `{rs485: {...}, rs232: {...}, gsm: {...}}`. SI la
respuesta es 200 ENTONCES el sistema DEBE mostrar un mensaje "Configuracion
guardada exitosamente". SI la respuesta es 422 ENTONCES el sistema DEBE
mostrar el mensaje de error del servidor SIN perder los cambios del
formulario. Cubre: RF-F14-02c.

## R4
CUANDO el admin hace clic en "Test RS485", "Test RS232" o "Test GSM", el
sistema DEBE enviar `POST /api/config/test/{port}` con el nombre del puerto
correspondiente. MIENTRAS la prueba se ejecuta, el boton DEBE mostrar un
indicador de carga y DEBE estar deshabilitado. SI la respuesta contiene
`"status": "ok"` ENTONCES el sistema DEBE mostrar un mensaje "Prueba exitosa"
en color verde junto al boton. SI la respuesta contiene `"status": "fail"`
ENTONCES el sistema DEBE mostrar el mensaje de error en color rojo junto al
boton. Cubre: RF-F14-02d.

## R5
CUANDO el admin navega a `/admin/config`, el sistema DEBE mostrar los
siguientes campos de configuracion adicionales debajo de las secciones de
puertos:

- "Session Timeout (minutos)": campo numerico, valor por defecto 15. Al hacer
  clic en "Guardar Session Timeout", el sistema DEBE enviar
  `PUT /api/setup/session` con `{session_timeout_minutes: <valor>}`.
- "Scale Timeout (segundos)": campo numerico entre 1 y 10, valor por defecto
  3. Al hacer clic en "Guardar Scale Timeout", el sistema DEBE enviar
  `PUT /api/setup/scale` con `{timeout_seconds: <valor>}`.

SI la respuesta de cualquiera de los dos PUT es 200 ENTONCES el sistema DEBE
mostrar un mensaje de exito. SI la respuesta es 422 ENTONCES el sistema DEBE
mostrar el mensaje de error. Cubre: RF-F14-02e.

## R6
CUANDO el admin navega a `/admin/config`, el sistema DEBE cargar los valores
actuales de session timeout y scale timeout desde `GET /api/config` y
pre-poblar los campos correspondientes. Cubre: RF-F14-02e.

## R7
CUANDO el admin navega a `/admin/backup`, el sistema DEBE cargar el historial
de los ultimos 10 backups via `GET /api/backup/status` y mostrarlos en una
tabla con las columnas: ID, Archivo, Tamano, Checksum Local, Copia USB,
Checksum USB, Error, Fecha. MIENTRAS carga, DEBE mostrar un indicador de
carga. SI la lista esta vacia, DEBE mostrar "No hay registros de backup".
Cubre: RF-F14-02f.

## R8
CUANDO el admin esta en `/admin/backup` y hace clic en el boton "Ejecutar
Backup", el sistema DEBE enviar `POST /api/backup/run`. SI la respuesta es
202 ENTONCES el sistema DEBE mostrar un mensaje "Backup iniciado en segundo
plano" y deshabilitar el boton por 30 segundos para evitar ejecuciones
multiples. MIENTRAS el boton esta deshabilitado, DEBE mostrar "Procesando..."
y un spinner. Cubre: RF-F14-02g.

## R9
SI `POST /api/backup/run` devuelve HTTP 4xx o 5xx ENTONCES el sistema DEBE
mostrar un mensaje de error SIN deshabilitar el boton. Cubre: RF-F14-02g.

## R10
CUANDO el admin navega a `/admin/backup`, el sistema DEBE mostrar un boton
"Refrescar" que recarga la tabla de backups via `GET /api/backup/status`.
Cubre: RF-F14-02h.

## R11
CUANDO el admin navega a `/admin/config`, los valores de baudrate, paridad,
data_bits y stop_bits DEBEN mostrarse en selects (dropdown) con valores
predefinidos y NO en campos de texto libre. Cubre: RF-F14-02a.
