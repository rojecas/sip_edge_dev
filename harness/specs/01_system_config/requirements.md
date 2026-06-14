# Requirements — system_config (EARS)

> Feature: Configuracion del Sistema — Puertos RS485/RS232 y GSM
> Covers: RF-015, RF-016, RF-017

## R1
CUANDO un cliente HTTP realiza `GET /api/config`, el sistema DEBE devolver la
configuracion actual de los tres puertos (rs485, rs232, gsm) como JSON con
status 200, incluyendo un campo `last_updated` con timestamp ISO 8601.

## R2
CUANDO un cliente HTTP realiza `PUT /api/config` con un body JSON valido, el
sistema DEBE persistir los cambios en `config.yaml` atomicamente y devolver la
configuracion actualizada con status 200.

## R3
CUANDO el sistema arranca (`src/main.py`), el sistema DEBE cargar la configuracion
desde `config.yaml` si el archivo existe, y construir una instancia del modelo
de dominio con esos valores.

## R4
CUANDO `config.yaml` no existe en el arranque del sistema, el sistema DEBE
crearlo con los valores por defecto del EdgeBox-RPI-200:
- rs485: path=/dev/ttyACM0, baudrate=115200, parity=N, data_bits=8, stop_bits=1
- rs232: path=/dev/ttyACM1, baudrate=115200, parity=N, data_bits=8, stop_bits=1
- gsm: modem_index=0

## R5
SI `PUT /api/config` recibe un valor de `baudrate` que no pertenece al conjunto
{300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200} ENTONCES el sistema
DEBE devolver status 422 con un mensaje de error descriptivo.

## R6
SI `PUT /api/config` recibe un valor de `data_bits` que no pertenece al conjunto
{5, 6, 7, 8} ENTONCES el sistema DEBE devolver status 422 con un mensaje de error
descriptivo.

## R7
SI `PUT /api/config` recibe un valor de `parity` que no pertenece al conjunto
{N, E, O, M, S} ENTONCES el sistema DEBE devolver status 422 con un mensaje de
error descriptivo.

## R8
SI `PUT /api/config` recibe un valor de `stop_bits` que no pertenece al conjunto
{1.0, 1.5, 2.0} ENTONCES el sistema DEBE devolver status 422 con un mensaje de
error descriptivo.

## R9
SI `PUT /api/config` recibe un valor de `modem_index` que NO es un entero >= 0
ENTONCES el sistema DEBE devolver status 422 con un mensaje de error descriptivo.

## R10
CUANDO un cliente HTTP realiza `POST /api/config/test/rs485`, el sistema DEBE
intentar abrir el puerto serial configurado (path, baudrate, parity, data_bits,
stop_bits) y devolver `{"status": "ok"}` con status 200 si la apertura es
exitosa, o `{"status": "fail", "detail": "<mensaje>"}` con status 200 si
falla. El puerto DEBE cerrarse inmediatamente tras la prueba.

## R11
CUANDO un cliente HTTP realiza `POST /api/config/test/rs232`, el sistema DEBE
intentar abrir el puerto serial configurado (path, baudrate, parity, data_bits,
stop_bits) y devolver `{"status": "ok"}` con status 200 si la apertura es
exitosa, o `{"status": "fail", "detail": "<mensaje>"}` con status 200 si
falla. El puerto DEBE cerrarse inmediatamente tras la prueba.

## R12
CUANDO un cliente HTTP realiza `POST /api/config/test/gsm`, el sistema DEBE
ejecutar `mmcli -m <modem_index>` via subprocess y devolver `{"status": "ok"}`
con status 200 si el comando retorna exit_code 0, o `{"status": "fail",
"detail": "<mensaje>"}` con status 200 si el comando falla (exit_code != 0).

## R13
SI `POST /api/config/test/{port}` recibe un valor de `port` distinto de `rs485`,
`rs232`, o `gsm` ENTONCES el sistema DEBE devolver status 404 con un mensaje de
error descriptivo.

## R14
El modelo de dominio de configuracion DEBE ser un dataclass inmutable
(`frozen=True`) con tipos exactos. Cualquier modificacion DEBE producir una
nueva instancia.

## R15
Toda escritura a `config.yaml` DEBE realizarse escribiendo primero en un archivo
temporal y luego `os.replace()` (atomicidad en disco).

## R16
CUANDO la carga de `config.yaml` falla por formato YAML invalido, el sistema
DEBE reintentar con los defaults (R4) y registrar el error.
