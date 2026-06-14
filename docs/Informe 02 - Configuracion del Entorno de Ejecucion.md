
---
## Informe de Progreso 2: Configuracion del Entorno de Ejecucion — EdgeBox-RPI-200

> **Alcance:** SO actual, DB, Python/dependencias, SIP-Edge, llama.cpp, config.yaml, servicios de software.
---

### 1. Sistema Operativo (Estado Actual) - Estado: COMPLETADO



El SO fue actualizado a Debian 13 (Trixie) — ver Informe 01.

| Componente | Detalle |
|------------|---------|
| **Sistema Operativo** | Debian GNU/Linux 13 (trixie) |
| **Arquitectura** | aarch64 (64-bit) |
| **Kernel** | Linux 6.12.75+rpt-rpi-v8 #1 SMP PREEMPT aarch64 |
| **Dispositivo** | EdgeBox-RPI-200 (Raspberry Pi Compute Module 4 Rev 1.1) |
| **CPU** | 4 x ARM Cortex-A72 @ 1.5 GHz |
| **RAM** | 7.6 GB total (948 MB CPU, 76 MB GPU) |
| **Almacenamiento** | 32 GB eMMC (`/dev/mmcblk0p2`, 14 GB usados, 14 GB libres) |
| **Swap** | 2.0 GB |
| **Hostname** | SIP-Edge |
| **Shell** | bash |

### Comandos de verificacion

```bash
cat /etc/os-release | grep PRETTY_NAME
# PRETTY_NAME="Debian GNU/Linux 13 (trixie)"

uname -m
# aarch64

free -h | grep Mem
# Mem: 7.6Gi total, ~650Mi used, ~6.0Gi free

df -h /
# /dev/mmcblk0p2  29G  14G  14G  49% /
```

---

### 2. Usuarios del Sistema y Permisos - Estado: COMPLETADO

La creacion de usuarios, asignacion de grupos y credenciales de acceso, estan documentadas en el
Informe 01 seccion 2. Aqui se presenta el resumen del estado actual.

### Usuarios

| Usuario | Rol | Shell | sudo | dialout |
|---------|-----|-------|------|---------|
| `root` | Superusuario | `/bin/bash` | — | — |
| `admin` | Administrador del dispositivo | `/bin/bash` | Si | — |
| `sipedge` | Usuario de aplicacion (SIP-Edge) | `/bin/bash` | Si | Si |
| `bkmngr` | Backup Operator (respaldos BD) | `/bin/bash` | No | Si |

### Grupos del usuario `sipedge`

```
sipedge tty dialout sudo video plugdev users gpio i2c
```

| Grupo | Proposito |
|-------|-----------|
| `dialout` | Acceso a puertos seriales `/dev/ttyACM*` |
| `sudo` | Privilegios administrativos |
| `video` | Aceleracion grafica (DRM, framebuffer) |
| `plugdev` | Dispositivos USB (modem 4G) |
| `gpio` | Control de pines GPIO |
| `i2c` | Bus I2C (RTC, sensores) |
| `tty` | Acceso general a terminales |
| `users` | Grupo base de usuarios |

### Auto-login modo kiosco

Configurado en `/etc/lightdm/lightdm.conf`:

```ini
[Seat:*]
autologin-user=sipedge
autologin-user-timeout=0
```

### Acceso SSH

```bash
ssh -i <clave_privada> sipedge@192.168.1.42
```

---

### 3. Red y Conectividad  - Estado: COMPLETADO

> La configuracion detallada del modem 4G (comandos mmcli, nmcli, scripts de
> red) esta en el Informe 01 seccion 3.2. Aqui se presenta el resumen del estado actual.

### Interfaces de red

| Interfaz | Tipo | Estado | IP |
|----------|------|--------|-----|
| `eth0` | Ethernet | UP | 192.168.1.42/24 |
| `wwan0` | 4G LTE (Quectel EC25) | DOWN (sin plan de datos activo) | DHCP operador |
| `wlan0` | WiFi | No disponible | — |
| `lo` | Loopback | UP | 127.0.0.1/8 |

### Modem 4G LTE — Resumen

| Componente | Estado |
|------------|--------|
| Deteccion USB (ID `2c7c:0125`) | OK |
| Puertos: `ttyUSB0`–`ttyUSB3` | OK |
| Interfaz `wwan0` | OK |
| ModemManager | Activo |
| SIM Tigo Colombia (732103) | Detectada |
| Senal LTE | 89% |
| APN: `internet.tigo.com.co` | Configurado |
| Plan de datos activo | Pendiente |

### Comandos de verificacion

```bash
ip -br addr                     # Interfaces de red
mmcli -m 0                      # Estado del modem
mmcli -b 1                      # Estado del bearer
nmcli connection show Quectel-4G  # Configuracion 4G
```

### Scripts de gestion

| Script | Funcion |
|--------|---------|
| `/usr/local/bin/switch_network.sh status` | Estado de conexiones |
| `/usr/local/bin/switch_network.sh eth` | Solo Ethernet |
| `/usr/local/bin/switch_network.sh 4g` | Solo 4G |
| `/usr/local/bin/switch_network.sh dual` | Ethernet + 4G |
| `/usr/local/bin/send_sms.sh` | SMS de prueba |

---

## 4. Puertos Seriales — Configuracion de Software  - Estado: COMPLETADO

> La configuracion fisica de los puertos y permisos esta en el Informe 01
> seccion 3.3. Aqui se documenta la configuracion a nivel de aplicacion.

### Mapeo de puertos

| Puerto | Dispositivo | Proposito |
|--------|-------------|-----------|
| RS485 | `/dev/ttyACM0` | Bascula DINI ARGEO DFWLI-2 |
| RS232 | `/dev/ttyACM1` | PC externo |

### Permisos

Los puertos pertenecen a `root:dialout`. El usuario `sipedge` esta en el grupo
`dialout`, con acceso de lectura/escritura sin `sudo`.

```bash
ls -la /dev/ttyACM*
# crw-rw---- 1 root dialout 166, 0 Jun 14 09:33 /dev/ttyACM0
# crw-rw---- 1 root dialout 166, 1 Jun 14 09:33 /dev/ttyACM1
```

### Configuracion en `config.yaml`

La aplicacion SIP-Edge gestiona los parametros seriales via `config.yaml`:

```yaml
rs485:
  path: /dev/ttyACM0
  baudrate: 115200
  data_bits: 8
  parity: N
  stop_bits: 1.0

rs232:
  path: /dev/ttyACM1
  baudrate: 115200
  data_bits: 8
  parity: N
  stop_bits: 1.0
```

Los parametros pueden modificarse dinamicamente desde la API
(`GET/PUT /api/config`) sin reiniciar el servicio.

---

### 5. Base de Datos — MariaDB - Estado: COMPLETADO

### Instalacion

```bash
sudo apt install -y mariadb-server
sudo systemctl enable --now mariadb
```

### Configuracion

| Parametro | Valor |
|-----------|-------|
| **Version** | MariaDB 11.8.6 |
| **Puerto** | 3306 (localhost) |
| **Base de datos** | `sip_edge` |
| **Usuario de aplicacion** | `sip_user`@`localhost` |
| **Contrasena** | `sip_pass` |
| **Motor** | InnoDB |
| **Socket** | `/run/mysqld/mysqld.sock` |

### Creacion de la base de datos

```sql
CREATE DATABASE IF NOT EXISTS sip_edge;
CREATE USER IF NOT EXISTS 'sip_user'@'localhost' IDENTIFIED BY 'sip_pass';
GRANT ALL ON sip_edge.* TO 'sip_user'@'localhost';
FLUSH PRIVILEGES;
```

### Tablas (creadas por SQLAlchemy al iniciar SIP-Edge)

| Tabla | Contenido |
|-------|-----------|
| `users` | Usuarios del sistema (admin, operadores, corresponsales) |
| `haciendas` | Haciendas (fincas) |
| `suertes` | Suertes/Lotes (vinculadas a haciendas) |
| `weighings` | Registros de pesaje |
| `backup_logs` | Registro de ejecuciones de backup |

### Servicio

```bash
sudo systemctl status mariadb
# Active: active (running)
```

---

### 6. Python y Dependencias de la Aplicacion  - Estado: COMPLETADO

### Runtime

| Componente | Version | Ubicacion |
|------------|---------|-----------|
| **Python** | 3.13.5 | Sistema (`/usr/bin/python3`) |
| **pip** | 25.1.1 | Sistema |
| **Entorno virtual (venv)** | — | `/home/sipedge/sip_edge/venv` |
| **Repositorio** | — | `/home/sipedge/sip_edge` |

### Dependencias (venv)

```
annotated-types==0.7.0
anyio==4.13.0
bcrypt==4.2.1
certifi==2026.5.20
cffi==2.0.0
click==8.4.1
cryptography==44.0.0
ecdsa==0.19.2
fastapi==0.115.6
h11==0.16.0
httpcore==1.0.9
httptools==0.8.0
httpx==0.28.1
idna==3.18
passlib[bcrypt]==1.7.4
pyasn1==0.6.3
pycparser==3.0
pydantic==2.10.3
pydantic-settings==2.7.0
pydantic_core==2.27.1
PyMySQL==1.1.1
pyserial==3.5
python-dotenv==1.0.1
python-jose[cryptography]==3.3.0
PyYAML==6.0.2
rsa==4.9.1
six==1.17.0
SQLAlchemy==2.0.36
starlette==0.41.3
typing_extensions==4.15.0
uvicorn[standard]==0.34.0
websockets==14.1
```

### Resumen por categoria

| Categoria | Paquetes |
|-----------|----------|
| **Framework Web** | FastAPI, uvicorn, starlette |
| **ORM / BD** | SQLAlchemy, PyMySQL |
| **Autenticacion** | python-jose (JWT), passlib (hash), bcrypt, cryptography |
| **Validacion** | Pydantic, pydantic-settings |
| **Hardware** | pyserial (RS232/RS485) |
| **Utilidades** | PyYAML, python-dotenv, httpx, websockets |

### Variables de entorno (`.env`)

Archivo: `/home/sipedge/sip_edge/.env`

```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=sip_edge
DB_USER=sip_user
DB_PASSWORD=sip_pass
JWT_SECRET_KEY=sip_edge_jwt_secret_prod
ADMIN_DEFAULT_PASSWORD=admin
DEV_MODE=false
```

| Variable | Proposito |
|----------|-----------|
| `DB_HOST` | Host de MariaDB (localhost) |
| `DB_PORT` | Puerto de MariaDB |
| `DB_NAME` | Nombre de la base de datos |
| `DB_USER` | Usuario de BD |
| `DB_PASSWORD` | Contrasena de BD |
| `JWT_SECRET_KEY` | Clave para firmar tokens JWT |
| `ADMIN_DEFAULT_PASSWORD` | Contrasena inicial del admin |
| `DEV_MODE` | `false` → hardware real activo (RS485, RS232, GSM) |

---

### 7. Servicio SIP-Edge (systemd) - Estado: COMPLETADO

La aplicacion SIP-Edge se ejecuta como servicio systemd con inicio automatico.

### Archivo de unidad: `/etc/systemd/system/sip-edge.service`

```ini
[Unit]
Description=SIP-Edge Backend
After=network.target mariadb.service
Requires=mariadb.service

[Service]
Type=simple
User=sipedge
WorkingDirectory=/home/sipedge/sip_edge
EnvironmentFile=/home/sipedge/sip_edge/.env
ExecStart=/home/sipedge/sip_edge/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
WatchdogSec=30

[Install]
WantedBy=multi-user.target
```

> `WatchdogSec=30` agregado el 2026-06-14 para integracion con el hardware
> watchdog (ver Informe 01 seccion 3.4 y `[RNF-003]`). Efectivo a nivel de
> sistema (systemd reinicia el servicio si se cuelga). La notificacion
> `WATCHDOG=1` via `sd_notify()` requiere `Type=notify` y codigo adicional
> en la aplicacion (mejora futura).

### Dependencias

```
mariadb.service ─────┐
network.target ──────┤
                     ├──→ sip-edge.service
                     │
ModemManager.service ┘
```

### Script de respaldo (`scripts/backup.py`)

Script standalone ejecutable via cron para respaldo diario de la base de datos:

- Ejecuta `mysqldump` contra `sip_edge` y comprime con gzip.
- Rota archivos manteniendo maximo 30 dias (FIFO).
- Copia a USB (`/mnt/backup_usb`) si esta montado, con verificacion CRC32.
- Registra cada ejecucion en la tabla `backup_logs` (exito o fallo).

```bash
# Ejecucion manual
cd /home/sipedge/sip_edge
python scripts/backup.py

# Configuracion cron (diario a las 23:55)
55 23 * * * cd /home/sipedge/sip_edge && python scripts/backup.py >> /var/log/sip_edge_backup.log 2>&1
```

### Comandos de gestion

```bash
sudo systemctl start sip-edge      # Iniciar
sudo systemctl stop sip-edge       # Detener
sudo systemctl restart sip-edge    # Reiniciar
sudo systemctl status sip-edge     # Ver estado
sudo journalctl -u sip-edge -f     # Logs en tiempo real
```

### API Endpoints (puerto 8000)

| Metodo | Ruta | Funcion |
|--------|------|---------|
| GET | `/` | Health check basico |
| GET | `/health` | Health check |
| POST | `/api/auth/login` | Login (JWT) |
| GET/POST | `/api/users` | CRUD de usuarios (admin) |
| PUT | `/api/users/{id}` | Actualizar usuario |
| CRUD | `/api/haciendas` | Gestion de haciendas |
| CRUD | `/api/suertes` | Gestion de suertes |
| CRUD | `/api/weighings` | Captura de pesaje |
| POST | `/api/weighings/reset` | Reset de formulario |
| PUT | `/api/setup/session` | Configurar timeout de sesion |
| PUT | `/api/setup/scale` | Configurar timeout de bascula |
| GET/PUT | `/api/config` | Configuracion del sistema |
| POST | `/api/config/test/{port}` | Prueba de puerto serial/GSM |
| GET | `/api/backup/status` | Estado de respaldos (ultimos 10 registros) |
| POST | `/api/backup/run` | Disparar respaldo manual |

---

### 8. llama.cpp — Motor de Inferencia LLM - Estado: COMPLETADO


> Ultima actualizacion: 05 de junio de 2026 (b8763 → b9632)

### Compilacion

```bash
git clone --depth 1 https://github.com/ggerganov/llama.cpp llama.cpp_build
cd llama.cpp_build
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j1   # -j1 recomendado para CM4 (4 cores, RAM limitada)
sudo cp bin/* /usr/local/bin/
```

### Configuracion de hardware detectada por CMake

```
CMAKE_SYSTEM_PROCESSOR: aarch64
GGML_SYSTEM_ARCH: ARM
ARM flags: -mcpu=cortex-a72+crc+nodotprod+noi8mm+nosve+nosme
FMA: yes
DOTPROD: no (Cortex-A72 no soporta)
I8MM: no (Cortex-A72 no soporta)
SVE: no (Cortex-A72 no soporta)
```

### Dependencias de compilacion

| Paquete | Version | Proposito |
|---------|---------|-----------|
| `build-essential` | 12.12 | Compilador GCC, make, headers |
| `cmake` | 3.31.6 | Sistema de construccion |
| `libssl-dev` | 3.5.5 | SSL/TLS para llama-server |

### Historial de versiones

| Fecha | Build | ggml | Binarios | Cambios clave |
|-------|-------|------|----------|---------------|
| 11/04/2026 | b8763 (ff5ef8278) | v0.14.0 | 42 | Instalacion inicial |
| **14/06/2026** | **b9632 (1fd6dfe)** | **v0.15.1** | **49** | **Actualizacion actual** |

### Cambios en la actualizacion (b8763 → b9632, +870 commits)

| Categoria | Cambio |
|-----------|--------|
| **ggml** | v0.14.0 → v0.15.1 — mejoras de rendimiento en backend CPU ARM |
| **ggml-cpu** | Fix en `rms_norm_back` para aliasing de buffers |
| **CPU Backend** | Nuevo op `COL2IM_1D` cuantizable para convolucion 1D |
| **Server** | PWA support, limpieza de static assets, fix reasoning budget, prompt logging |
| **Multi-modal** | Batching API para imagenes/audio (mtmd) |
| **Jinja templates** | Fix en split/replace/slice para compatibilidad con mas modelos |

### Binarios principales (49 en `/usr/local/bin/`)

| Binario | Proposito |
|---------|-----------|
| `llama-server` | Servidor HTTP API compatible OpenAI |
| `llama-cli` | CLI interactivo para chat |
| `llama-bench` | Benchmark de rendimiento |
| `llama-perplexity` | Evaluacion de perplejidad |
| `llama-quantize` | Cuantizacion de modelos |
| `llama-embedding` | Generacion de embeddings |
| `llama-gguf` | Utilidad de archivos GGUF |
| `llama-mtmd-cli` | CLI multi-modal (texto + imagen + audio) |
| `llama-simple-chat` | Chat simple sin servidor |

### Version actual

```
llama-cli --version
# version: 1 (1fd6dfe)
# build: b1-1fd6dfe
# built with GNU 14.2.0 for Linux aarch64
```

### Verificacion de inferencia

```bash
$ llama-cli -m /home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf -p "Hello" -n 10

build      : b1-1fd6dfe
model      : qwen2.5-1.5b-instruct-q4_k_m.gguf
modalities : text

> Hello
Hello! How can I assist you today?

[ Prompt: 7.7 t/s | Generation: 3.6 t/s ]
```

### Modelos descargados (`/home/models/`)

| Modelo | Tamano | Cuantizacion | Parametros | Tipo |
|--------|--------|--------------|------------|------|
| `qwen2.5-1.5b-instruct-q4_k_m.gguf` | 1.1 GB | Q4_K_M | 1.5B | Instruct (chat) |
| `gemma-4-E2B-it-Q4_K_M.gguf` | 2.9 GB | Q4_K_M | 2B | Instruct (chat) |
| `Qwen3.5-2B-UD-Q2_K_XL.gguf` | 922 MB | Q2_K_XL | 2B | Ultra-denso |

**Total ocupado:** ~4.9 GB

### Comando de ejemplo — servidor

```bash
# Modelo ligero (922 MB)
llama-server \
  -m /home/models/Qwen3.5-2B-UD-Q2_K_XL.gguf \
  -c 2048 \
  --host 0.0.0.0 \
  --port 8080

# Modelo balanceado (1.1 GB)
llama-server \
  -m /home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  -c 4096 \
  --host 0.0.0.0 \
  --port 8080
```

### Consideraciones de rendimiento

Con 7.6 GB de RAM y los modelos disponibles (<= 2.9 GB), el sistema tiene
entre 4.7 y 6.7 GB libres para SO, MariaDB, SIP-Edge y llama-server
simultaneamente. El Cortex-A72 no tiene DOTPROD, I8MM ni SVE, pero si FMA.
Rendimiento observado: ~3.6 t/s en generacion para modelos Q4_K_M de ~1.5B.

---

### 9. Archivo de Configuracion — config.yaml - Estado: COMPLETADO

Generado automaticamente por SIP-Edge en el primer arranque.
Ubicacion: `/home/sipedge/sip_edge/config.yaml`.

### Contenido actual

```yaml
gsm:
  modem_index: 0
last_updated: '2026-06-14T15:09:07.196008+00:00'
rs232:
  baudrate: 115200
  data_bits: 8
  parity: N
  path: /dev/ttyACM1
  stop_bits: 1.0
rs485:
  baudrate: 115200
  data_bits: 8
  parity: N
  path: /dev/ttyACM0
  stop_bits: 1.0
scale:
  timeout_seconds: 3
session:
  session_timeout_minutes: 15
backup:
  usb_mount_path: /mnt/backup_usb
  local_dir: /home/bkmngr/backups
  keep_days: 30
```

### Parametros

| Seccion | Parametro | Valor | Descripcion |
|---------|-----------|-------|-------------|
| `rs485` | `path` | `/dev/ttyACM0` | Puerto de la bascula |
| `rs485` | `baudrate` | `115200` | Velocidad serial |
| `rs485` | `parity` | `N` | Sin paridad |
| `rs485` | `data_bits` | `8` | 8 bits de datos |
| `rs485` | `stop_bits` | `1.0` | 1 bit de parada |
| `rs232` | `path` | `/dev/ttyACM1` | Puerto del PC externo |
| `rs232` | `baudrate` | `115200` | Velocidad serial |
| `gsm` | `modem_index` | `0` | Indice en ModemManager |
| `scale` | `timeout_seconds` | `3` | Timeout de respuesta de bascula |
| `session` | `session_timeout_minutes` | `15` | Bloqueo por inactividad |
| `backup` | `usb_mount_path` | `/mnt/backup_usb` | Ruta de montaje del USB de respaldo |
| `backup` | `local_dir` | `/home/bkmngr/backups` | Directorio local de respaldos |
| `backup` | `keep_days` | `30` | Dias de retencion (rotacion FIFO) |

---

### 10. Servicios del Sistema - Estado: COMPLETADO

| Servicio | Estado | Auto-start | Funcion |
|----------|--------|------------|---------|
| `mariadb.service` | Active | Enabled | Base de datos MariaDB 11.8.6 |
| `sip-edge.service` | Active | Enabled | Backend SIP-Edge (FastAPI + uvicorn) |
| `ModemManager.service` | Active | — | Gestion del modem 4G |
| `NetworkManager.service` | Active | — | Gestion de conexiones de red |
| `ssh.service` | Active | — | Acceso SSH remoto |
| `cron.service` | Active | — | Tareas programadas |
| `systemd-timesyncd.service` | Active | — | Sincronizacion NTP |
| `save-hwclock.service` | Active | — | Persistencia del RTC PCF8563 |
| `quectel-init.service` | Active | — | Inicializacion del modem al arranque |

### Dependencias entre servicios

```
mariadb.service ─────┐
network.target ──────┤
                     ├──→ sip-edge.service
                     │
ModemManager.service ┘
```

---

### 11. Resumen de Archivos Configurados

| Archivo | Proposito | Informe |
|---------|-----------|---------|
| `/boot/firmware/config.txt` | Overlays RTC, I2C, UART, GPIO, WDT | Informe 01 |
| `/etc/systemd/system/save-hwclock.service` | Sincronizacion RTC | Informe 01 |
| `/etc/NetworkManager/system-connections/Quectel-4G.nmconnection` | Conexion 4G | Informe 01 |
| `/usr/local/bin/quectel-init.sh` | Inicializacion modem | Informe 01 |
| `/etc/systemd/system/quectel-init.service` | Servicio inicializacion modem | Informe 01 |
| `/usr/local/bin/switch_network.sh` | Conmutacion de red | Informe 01 |
| `/usr/local/bin/send_sms.sh` | Envio de SMS de prueba | Informe 01 |
| `/etc/lightdm/lightdm.conf` | Auto-login modo kiosco | Informe 01 |
| `/etc/polkit-1/localauthority/50-local.d/10-modemmanager.pkla` | Permisos PolicyKit modem | Informe 01 |
| `/etc/systemd/system.conf` | RuntimeWatchdogSec=30 | Informe 01 |
| `/etc/systemd/system.conf.d/50-watchdog-30s.conf` | Override WDT 30s | Informe 01 |
| `/etc/systemd/system/sip-edge.service` | Servicio SIP-Edge + WatchdogSec=30 | Informe 02 |
| `/home/sipedge/sip_edge/.env` | Variables de entorno SIP-Edge | Informe 02 |
| `/home/sipedge/sip_edge/config.yaml` | Configuracion de hardware y sesion | Informe 02 |
| `/usr/local/bin/llama-*` | Binarios llama.cpp v9632 (49 herramientas) | Informe 02 |
| `/home/models/*.gguf` | Modelos GGUF (~4.9 GB, 3 modelos) | Informe 02 |

---

### 12. Conclusion

El entorno de ejecucion del EdgeBox-RPI-200 esta completamente configurado
y operativo:

- **SO** Debian 13 aarch64 con kernel 6.12, 7.6 GB RAM disponibles.
- **BD** MariaDB 11.8 con base `sip_edge` y usuario de aplicacion.
- **SIP-Edge** ejecutandose como servicio systemd con auto-inicio, 15
  endpoints REST en puerto 8000.
- **Watchdog** de hardware a 30s integrado con systemd (`[RNF-003]`).
- **llama.cpp** v9632 con 49 herramientas y 3 modelos GGUF (~4.9 GB).
- **Red** Ethernet activa (192.168.1.42), modem 4G configurado.

Los perifericos de hardware (RTC, RS485, RS232, modem 4G, WDT, UPS) estan
documentados en el **Informe 01 — Configuracion de Hardware**.
---
