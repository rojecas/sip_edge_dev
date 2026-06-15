# Requirements — backup_system (EARS)

> Feature: Sistema de Respaldos y Exportacion
> Covers: RF-018, RF-019, RF-023, RF-024, RF-025
> Depends on: feature 1 (system_config) — indirectly for config.yaml infrastructure

---

## Configuracion de backup (config.yaml)

### R1
El sistema DEBE leer la seccion `backup` de `config.yaml` con los campos
`usb_mount_path` (string), `local_dir` (string) y `keep_days` (int). SI la
seccion `backup` no existe en `config.yaml`, el sistema DEBE usar valores por
defecto:
`usb_mount_path="/mnt/backup_usb"`, `local_dir="/home/bkmngr/backups"`,
`keep_days=30`.

### R2
El sistema DEBE incluir un dataclass congelado `BackupConfig` en `src/config.py`
con los campos `usb_mount_path: str`, `local_dir: str`, `keep_days: int`.

### R3
La funcion `load_config` en `src/config.py` DEBE ser extendida para devolver
tambien `BackupConfig` (ademas de `SystemConfig`, `SessionConfig` y
`ScaleConfig`), leyendo la seccion `backup` de `config.yaml`.

### R4
SI `keep_days` es menor o igual a 0, el sistema DEBE usar el valor por defecto
(30) y registrar un warning en el log.

---

## Volcado de base de datos

### R5
CUANDO se ejecuta el proceso de backup, el sistema DEBE invocar `mysqldump`
contra la base de datos `sip_edge` usando las variables de entorno `DB_HOST`,
`DB_PORT`, `DB_USER`, `DB_PASSWORD` y `DB_NAME`. La salida de `mysqldump` DEBE
ser comprimida con gzip y guardada en `local_dir` con nombre de archivo
`backup_YYYYMMDD_HHMMSS.sql.gz` usando la fecha/hora actual UTC.

### R6
SI `mysqldump` falla (exit code != 0), el sistema DEBE capturar el mensaje de
error de stderr, registrarlo via logging y en la tabla `backup_logs`, y NO DEBE
crear un archivo de backup corrupto.

### R7
SI el directorio `local_dir` no existe, el sistema DEBE crearlo antes de escribir
el archivo de backup.

---

## Rotacion FIFO

### R8
DESPUES de generar un backup exitoso, el sistema DEBE eliminar los archivos mas
antiguos del directorio `local_dir` hasta que el numero de archivos `.sql.gz` no
exceda `keep_days`. La antiguedad DEBE determinarse por la fecha de modificacion
(`st_mtime`) del archivo.

### R9
La rotacion DEBE eliminar exclusivamente archivos con extension `.sql.gz` en
`local_dir`. Archivos con otras extensiones NO DEBEN ser afectados.

---

## Copia a USB con verificacion CRC32

### R10
DESPUES de generar un backup exitoso y ejecutar la rotacion, el sistema DEBE
verificar si el directorio `usb_mount_path` existe. SI existe, el sistema DEBE
copiar el archivo de backup generado a `usb_mount_path`.

### R11
TRAS copiar el archivo a `usb_mount_path`, el sistema DEBE calcular el CRC32 del
archivo local y del archivo copiado en USB usando `zlib.crc32`. SI los CRC32 no
coinciden, el sistema DEBE registrar un error en el log y en la tabla
`backup_logs`, indicando que la copia al USB fallo la verificacion de integridad.

### R12
SI `usb_mount_path` no existe en el momento del backup, el sistema DEBE registrar
un mensaje informativo en el log y continuar sin error. La ausencia de USB NO
DEBE interrumpir el proceso de backup local.

---

## Registro en base de datos

### R13
El sistema DEBE incluir un modelo ORM `BackupLog` en `src/models.py` mapeado a
la tabla `backup_logs` con las siguientes columnas: `id` (BIGINT PK
autoincrement), `filename` (VARCHAR 255), `file_size` (BIGINT, bytes),
`local_checksum` (VARCHAR 8, CRC32 hex), `usb_copied` (BOOLEAN),
`usb_checksum` (VARCHAR 8 nullable, CRC32 hex en USB si aplica), `error_message`
(TEXT nullable), `created_at` (TIMESTAMP con default CURRENT_TIMESTAMP).

### R14
CUANDO se ejecuta un backup, el sistema DEBE insertar un registro en
`backup_logs` con los campos `filename`, `file_size`, `local_checksum`,
`usb_copied`, `usb_checksum` y `error_message` correspondientes al resultado de
la operacion.

### R15
CUANDO el sistema arranca (lifespan de FastAPI), el sistema DEBE crear la tabla
`backup_logs` si esta no existe, usando el metadata de SQLAlchemy
(`Base.metadata.create_all()`).

---

## Script standalone de backup

### R16
El sistema DEBE proporcionar un script standalone `scripts/backup.py` que, al ser
ejecutado, realice el backup completo (dump + rotacion + copia USB + registro en
DB) y termine con exit code 0 en caso de exito o exit code != 0 en caso de
fallo.

### R17
El script `scripts/backup.py` DEBE leer las variables de entorno de base de datos
y la ruta de `config.yaml` de las mismas variables de entorno que la aplicacion
principal (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`,
`CONFIG_PATH` con fallback `config.yaml`).

### R18
El script `scripts/backup.py` DEBE ser ejecutable directamente con
`python scripts/backup.py` y NO DEBE requerir argumentos de linea de comandos.

---

## API endpoints

### R19
CUANDO un cliente HTTP autenticado con rol `admin` realiza `GET /api/backup/status`
sin parametros, el sistema DEBE devolver status 200 con un JSON que contenga los
ultimos 10 registros de la tabla `backup_logs` ordenados por `created_at`
descendente. Cada registro DEBE incluir todos los campos de `BackupLog` excepto
`error_message` cuando este sea null.

### R20
CUANDO un cliente HTTP autenticado con rol `admin` realiza `POST /api/backup/run`,
el sistema DEBE iniciar el proceso de backup en background usando
`BackgroundTasks` de FastAPI y devolver inmediatamente status 202 con
`{"status": "accepted", "message": "Backup started"}`.

### R21
SI `GET /api/backup/status` o `POST /api/backup/run` reciben una peticion sin
token valido, el sistema DEBE devolver status 401. Si el token es valido pero el
rol no es `admin`, el sistema DEBE devolver status 403.

### R22
CUANDO el backup en background iniciado via `POST /api/backup/run` finaliza
(exito o fallo), el sistema DEBE registrar el resultado en la tabla
`backup_logs`. Si el backup en background falla, el error DEBE quedar registrado
en `backup_logs.error_message`.

---

## Seguridad

### R23
Las credenciales de base de datos usadas para `mysqldump` DEBEN ser leidas
exclusivamente de variables de entorno. El sistema NO DEBE hardcodear
credenciales en el codigo fuente ni en `config.yaml`.

### R24
La contrasena de `DB_PASSWORD` NO DEBE aparecer en los logs ni en la tabla
`backup_logs`. El sistema DEBE usar `subprocess.Popen` con `stdin` para pasar la
contrasena a `mysqldump` en lugar de pasarla como argumento de linea de comandos
(visible en `ps aux`).
