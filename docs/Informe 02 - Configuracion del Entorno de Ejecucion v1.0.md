
---

## 📄 Informe de Progreso 2: Configuración del Entorno de Ejecución del **EdgeBox-RPI-200**

---

## 1. Sistema Operativo

### Estado: ✅ COMPLETADO

El sistema operativo instalado es **Raspberry Pi OS 64-bit (Debian 13 — Trixie)**, resultado de la migración documentada en el Informe 01. La arquitectura es completamente `aarch64`, liberando el acceso a los 8 GB de RAM del Compute Module 4.

### Resumen

| Componente | Detalle |
|------------|---------|
| **Sistema Operativo** | Debian GNU/Linux 13 (trixie) |
| **Arquitectura** | aarch64 (64-bit) |
| **Kernel** | Linux 6.12.75+rpt-rpi-v8 #1 SMP PREEMPT aarch64 |
| **Dispositivo** | EdgeBox-RPI-200 (Raspberry Pi Compute Module 4 Rev 1.1) |
| **CPU** | 4 × ARM Cortex-A72 @ 1.5 GHz |
| **RAM** | 7.6 GB total (948 MB asignados a CPU, 76 MB a GPU) |
| **Almacenamiento** | 32 GB eMMC (`/dev/mmcblk0p2`, 14 GB usados, 14 GB libres) |
| **Swap** | 2.0 GB |
| **Hostname** | SIP-Edge |
| **Shell** | bash |

### Comandos de verificación:
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

## 2. Usuarios del Sistema y Permisos

### Estado: ✅ COMPLETADO

Se definieron tres usuarios con propósitos diferenciados:

| Usuario | Rol | Shell | Grupo `sudo` | Grupo `dialout` |
|---------|-----|-------|--------------|-----------------|
| `root` | Superusuario del sistema | `/bin/bash` | — | — |
| `admin` | Administrador del dispositivo | `/bin/bash` | ✅ | — |
| `sipedge` | Usuario de aplicación (corre el servicio SIP-Edge) | `/bin/bash` | ✅ | ✅ |

### Grupos del usuario `sipedge`:

```
sipedge tty dialout sudo video plugdev users gpio i2c
```

| Grupo | Propósito |
|-------|-----------|
| `dialout` | Acceso a puertos seriales `/dev/ttyACM*` |
| `tty` | Acceso general a terminales |
| `sudo` | Privilegios administrativos |
| `video` | Aceleración gráfica (DRM, framebuffer) |
| `plugdev` | Dispositivos USB (módem 4G) |
| `gpio` | Control de pines GPIO |
| `i2c` | Bus I2C (RTC, sensores) |
| `users` | Grupo base de usuarios |

### Auto-login en modo kiosco:

Configurado en `/etc/lightdm/lightdm.conf`:

```ini
[Seat:*]
autologin-user=sipedge
autologin-user-timeout=0
```

### Credenciales de acceso (SSH):

```bash
ssh -i <clave_privada> sipedge@192.168.1.42
```

---

## 3. Red y Conectividad

### Estado: ✅ COMPLETADO

### Interfaces de red:

| Interfaz | Tipo | Estado | IP |
|----------|------|--------|-----|
| `eth0` | Ethernet | UP | 192.168.1.42/24 |
| `wwan0` | 4G LTE (Quectel EC25) | DOWN (sin plan de datos activo) | Asignada por DHCP de operador |
| `wlan0` | WiFi | No disponible | — |
| `lo` | Loopback | UP | 127.0.0.1/8 |

### Módem 4G LTE — Quectel EC25:

El módem está detectado y configurado por ModemManager. No hay conexión de datos activa al momento de este informe (plan de datos pendiente de activación en Tigo).

| Componente | Estado | Detalle |
|------------|--------|---------|
| Detección USB | ✅ | ID `2c7c:0125` |
| Puertos seriales | ✅ | `ttyUSB0` (ignored), `ttyUSB1` (gps), `ttyUSB2` (at), `ttyUSB3` (at) |
| Interfaz de red | ✅ | `wwan0` creada |
| ModemManager | ✅ | Módem gestionado como `/org/.../Modem/0` |
| SIM card | ✅ | Tigo Colombia (operador 732103) |
| Señal LTE | ✅ | 89% (última medición) |
| APN | ✅ | `internet.tigo.com.co` |

### Comandos de verificación:
```bash
# Interfaces de red
ip -br addr

# Estado del módem
mmcli -m 0

# Estado del bearer (conexión de datos)
mmcli -b 1

# Configuración de red 4G
nmcli connection show Quectel-4G
```

### Scripts de gestión de red:

| Script | Función |
|--------|---------|
| `/usr/local/bin/switch_network.sh status` | Muestra estado de conexiones |
| `/usr/local/bin/switch_network.sh eth` | Activa solo Ethernet |
| `/usr/local/bin/switch_network.sh 4g` | Activa solo 4G |
| `/usr/local/bin/switch_network.sh dual` | Activa Ethernet + 4G simultáneos |
| `/usr/local/bin/send_sms.sh` | Envía SMS de prueba |

### Servicios de red activos:

| Servicio | Estado | Función |
|----------|--------|---------|
| `ModemManager.service` | ✅ Activo | Gestión del módem 4G |
| `NetworkManager.service` | ✅ Activo | Gestión de conexiones de red |
| `ssh.service` | ✅ Activo | Acceso remoto seguro |

### Archivos de configuración de red:
- `/etc/NetworkManager/system-connections/Quectel-4G.nmconnection` — Conexión 4G LTE
- `/etc/polkit-1/localauthority/50-local.d/10-modemmanager.pkla` — Permisos PolicyKit para control del módem sin sudo

---

## 4. Puertos Seriales Industriales RS232 / RS485

### Estado: ✅ COMPLETADO

El EdgeBox-RPI-200 expone dos puertos USB-serial nativos con el siguiente mapeo:

| Puerto Físico | Dispositivo | Propósito |
|---------------|-------------|-----------|
| RS485 | `/dev/ttyACM0` | Comunicación con báscula DINI ARGEO DFWLI-2 |
| RS232 | `/dev/ttyACM1` | Transmisión de datos a PC externo |

### Permisos:

Los puertos pertenecen a `root:dialout`. El usuario `sipedge` está en el grupo `dialout`, por lo que tiene acceso de lectura/escritura sin necesidad de `sudo`.

```bash
ls -la /dev/ttyACM*
# crw-rw---- 1 root dialout 166, 0 Jun 14 09:33 /dev/ttyACM0
# crw-rw---- 1 root dialout 166, 1 Jun 14 09:33 /dev/ttyACM1
```

### Configuración de parámetros por defecto (`config.yaml`):

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

### Puertos adicionales del módem 4G:

| Dispositivo | Función |
|-------------|---------|
| `/dev/ttyUSB0` | Puerto QMI (ignorado por ModemManager) |
| `/dev/ttyUSB1` | GPS NMEA |
| `/dev/ttyUSB2` | Comandos AT |
| `/dev/ttyUSB3` | Comandos AT |

---

## 5. Base de Datos — MariaDB

### Estado: ✅ COMPLETADO

### Instalación:

MariaDB 11.8.6 fue actualizado desde los repositorios oficiales de Debian 13 (trixie) el 14 de junio de 2026.

```bash
sudo apt install -y mariadb-server
sudo systemctl enable --now mariadb
```

### Configuración:

| Parámetro | Valor |
|-----------|-------|
| **Versión** | MariaDB 11.8.6 |
| **Puerto** | 3306 (localhost) |
| **Base de datos** | `sip_edge` |
| **Usuario de aplicación** | `sip_user`@`localhost` |
| **Contraseña** | `sip_pass` |
| **Motor** | InnoDB |
| **Socket** | `/run/mysqld/mysqld.sock` |

### Creación de la base de datos:
```sql
CREATE DATABASE IF NOT EXISTS sip_edge;
CREATE USER IF NOT EXISTS 'sip_user'@'localhost' IDENTIFIED BY 'sip_pass';
GRANT ALL ON sip_edge.* TO 'sip_user'@'localhost';
FLUSH PRIVILEGES;
```

### Tablas (creadas automáticamente por SQLAlchemy al iniciar SIP-Edge):
- `users` — Usuarios del sistema (admin, operadores, corresponsales)
- `haciendas` — Haciendas (fincas)
- `suertes` — Suertes/Lotes (vinculadas a haciendas)
- `weighings` — Registros de pesaje

### Servicio:
```bash
sudo systemctl status mariadb
# Active: active (running)
```

---

## 6. Python y Dependencias de la Aplicación

### Estado: ✅ COMPLETADO

### Runtime:

| Componente | Versión | Ubicación |
|------------|---------|-----------|
| **Python** | 3.13.5 | Sistema (`/usr/bin/python3`) |
| **pip** | 25.1.1 | Sistema |
| **Entorno virtual (venv)** | — | `/home/sipedge/sip_edge/venv` |
| **Repositorio** | — | `/home/sipedge/sip_edge` |

### Dependencias instaladas (venv):

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

### Resumen por categoría:

| Categoría | Paquetes |
|-----------|----------|
| **Framework Web** | FastAPI, uvicorn, starlette |
| **ORM / BD** | SQLAlchemy, PyMySQL |
| **Autenticación** | python-jose (JWT), passlib (hash), bcrypt, cryptography |
| **Validación** | Pydantic, pydantic-settings |
| **Hardware** | pyserial (RS232/RS485) |
| **Utilidades** | PyYAML, python-dotenv, httpx, websockets |

### Variables de entorno (`.env`):

Archivo ubicado en `/home/sipedge/sip_edge/.env`:

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

| Variable | Propósito |
|----------|-----------|
| `DB_HOST` | Host de MariaDB (localhost) |
| `DB_PORT` | Puerto de MariaDB |
| `DB_NAME` | Nombre de la base de datos |
| `DB_USER` | Usuario de base de datos |
| `DB_PASSWORD` | Contraseña de base de datos |
| `JWT_SECRET_KEY` | Clave secreta para firmar tokens JWT |
| `ADMIN_DEFAULT_PASSWORD` | Contraseña inicial del usuario admin |
| `DEV_MODE` | `false` → hardware real activo (RS485, RS232, GSM) |

---

## 7. Servicio SIP-Edge (systemd)

### Estado: ✅ COMPLETADO

La aplicación SIP-Edge se ejecuta como un servicio systemd que inicia automáticamente al arrancar el sistema.

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

[Install]
WantedBy=multi-user.target
```

### Dependencias del servicio:

```
mariadb.service → sip-edge.service
```

### Comandos de gestión:

```bash
sudo systemctl start sip-edge      # Iniciar
sudo systemctl stop sip-edge       # Detener
sudo systemctl restart sip-edge    # Reiniciar
sudo systemctl status sip-edge     # Ver estado
sudo journalctl -u sip-edge -f     # Ver logs en tiempo real
```

### API Endpoints expuestos (puerto 8000):

| Método | Ruta | Función |
|--------|------|---------|
| GET | `/` | Health check básico |
| GET | `/health` | Health check |
| POST | `/api/auth/login` | Login (JWT) |
| GET/POST | `/api/users` | CRUD de usuarios (admin) |
| PUT | `/api/users/{id}` | Actualizar usuario |
| CRUD | `/api/haciendas` | Gestión de haciendas |
| CRUD | `/api/suertes` | Gestión de suertes |
| CRUD | `/api/weighings` | Captura de pesaje |
| POST | `/api/weighings/reset` | Reset de formulario |
| PUT | `/api/setup/session` | Configurar timeout de sesión |
| PUT | `/api/setup/scale` | Configurar timeout de báscula |
| GET/PUT | `/api/config` | Configuración del sistema |
| POST | `/api/config/test/{port}` | Prueba de puerto serial/GSM |

---

## 8. llama.cpp — Motor de Inferencia LLM

### Estado: ✅ COMPLETADO

> **Última actualización:** 14 de junio de 2026 (actualizado de b8763 → b9632)

llama.cpp fue compilado desde el código fuente del repositorio oficial (`https://github.com/ggerganov/llama.cpp`) siguiendo el procedimiento estándar CMake. Los binarios resultantes se instalaron de forma global en `/usr/local/bin/`.

### Proceso de compilación:

```bash
git clone --depth 1 https://github.com/ggerganov/llama.cpp llama.cpp_build
cd llama.cpp_build
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j1   # -j1 recomendado para CM4 (4 cores, RAM limitada)
sudo cp bin/* /usr/local/bin/
```

### Configuración de hardware detectada por CMake:

```
CMAKE_SYSTEM_PROCESSOR: aarch64
GGML_SYSTEM_ARCH: ARM
ARM flags: -mcpu=cortex-a72+crc+nodotprod+noi8mm+nosve+nosme
FMA: yes
DOTPROD: no (Cortex-A72 no soporta)
I8MM: no (Cortex-A72 no soporta)
SVE: no (Cortex-A72 no soporta)
```

### Dependencias de compilación instaladas:

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| `build-essential` | 12.12 | Compilador GCC, make, headers |
| `cmake` | 3.31.6 | Sistema de construcción |
| `libssl-dev` | 3.5.5 | SSL/TLS para llama-server |

### Historial de versiones:

| Fecha | Build | ggml | Binarios | Cambios clave |
|-------|-------|------|----------|---------------|
| 11/04/2026 | b8763 (ff5ef8278) | v0.14.0 | 42 | Instalación inicial |
| **14/06/2026** | **b9632 (1fd6dfe)** | **v0.15.1** | **49** | **Actualización actual** |

### Cambios en esta actualización (b8763 → b9632, +870 commits):

| Categoría | Cambio |
|-----------|--------|
| **ggml** | v0.14.0 → v0.15.1 — mejoras de rendimiento y estabilidad en backend CPU ARM |
| **ggml-cpu** | Fix en `rms_norm_back` para aliasing de buffers |
| **CPU Backend** | Nuevo op `COL2IM_1D` cuantizable para convolución 1D |
| **Server** | PWA support, limpieza de static assets, fix reasoning budget, prompt logging |
| **Multi-modal** | Batching API para imágenes/audio (mtmd) |
| **Jinja templates** | Fix en split/replace/slice para compatibilidad con más modelos |

### Binarios instalados (49 herramientas en `/usr/local/bin/`):

| Binario | Propósito |
|---------|-----------|
| `llama-server` | Servidor HTTP con API compatible con OpenAI |
| `llama-cli` | CLI interactivo para chat |
| `llama-bench` | Benchmark de rendimiento de inferencia |
| `llama-perplexity` | Evaluación de perplejidad del modelo |
| `llama-quantize` | Cuantización de modelos |
| `llama-embedding` | Generación de embeddings |
| `llama-gguf` | Utilidad de manipulación de archivos GGUF |
| `llama-imatrix` | Cálculo de matriz de importancia |
| `llama-finetune` | Fine-tuning LoRA |
| `llama-tokenize` | Tokenización de texto |
| `llama-simple-chat` | Chat simple sin servidor |
| `llama-tts` | Text-to-speech |
| `llama-speculative` | Decodificación especulativa |
| `llama-parallel` | Inferencia paralela |
| `llama-retrieval` | RAG (Retrieval-Augmented Generation) |
| `llama-lookahead` | Decodificación lookahead |
| `llama-mtmd-cli` | CLI multi-modal unificado (texto + imagen + audio) |
| `llama-mtmd-debug` | Depuración de pipeline multi-modal |
| `llama-gemma3-cli` | ⚠️ **Deprecado** — redirige a `llama-mtmd-cli` |
| `llama-qwen2vl-cli` | ⚠️ **Deprecado** — redirige a `llama-mtmd-cli` |
| `llama-llava-cli` | ⚠️ **Deprecado** — redirige a `llama-mtmd-cli` |
| `llama-minicpmv-cli` | ⚠️ **Deprecado** — redirige a `llama-mtmd-cli` |
| `llama-q8dot` | ❌ Benchmark producto punto Q8 — requiere SIMD no disponible en Cortex-A72 |
| `llama-vdot` | ❌ Benchmark producto punto vectorial — requiere SIMD no disponible en Cortex-A72 |
| `...` | (24 herramientas adicionales) |

### Versión actual:

```
llama-cli --version
# version: 1 (1fd6dfe)
# build: b1-1fd6dfe
# built with GNU 14.2.0 for Linux aarch64
```

### Verificación de inferencia (post-actualización):

```bash
$ llama-cli -m /home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf -p "Hello" -n 10

build      : b1-1fd6dfe
model      : qwen2.5-1.5b-instruct-q4_k_m.gguf
modalities : text

> Hello
Hello! How can I assist you today?

[ Prompt: 7.7 t/s | Generation: 3.6 t/s ]
```

### Modelos descargados (`/home/models/`):

| Modelo | Tamaño | Cuantización | Parámetros | Tipo |
|--------|--------|--------------|------------|------|
| `qwen2.5-1.5b-instruct-q4_k_m.gguf` | 1.1 GB | Q4_K_M | 1.5B | Instruct (chat) |
| `gemma-4-E2B-it-Q4_K_M.gguf` | 2.9 GB | Q4_K_M | 2B | Instruct (chat) |
| `Qwen3.5-2B-UD-Q2_K_XL.gguf` | 922 MB | Q2_K_XL | 2B | Ultra-denso |

**Total ocupado:** ~4.9 GB

### Comando de ejemplo para ejecutar el servidor:

```bash
# Con el modelo más ligero (Qwen3.5-2B Q2_K_XL, 922 MB)
llama-server \
  -m /home/models/Qwen3.5-2B-UD-Q2_K_XL.gguf \
  -c 2048 \
  --host 0.0.0.0 \
  --port 8080

# Con el modelo balanceado (Qwen2.5 1.5B Q4_K_M, 1.1 GB)
llama-server \
  -m /home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  -c 4096 \
  --host 0.0.0.0 \
  --port 8080
```

### Consideraciones de rendimiento:

Con 7.6 GB de RAM y los modelos disponibles (≤ 2.9 GB), el sistema tiene entre **4.7 y 6.7 GB libres** para el sistema operativo, MariaDB, SIP-Edge y el servidor llama.cpp simultáneamente. El modelo Gemma 4 (2.9 GB) es el más pesado pero ofrece la mejor calidad. Se recomienda usar Qwen3.5-2B (922 MB) o Qwen2.5 1.5B (1.1 GB) para desarrollo y reservar Gemma 4 para contextos que requieran mayor precisión.

El Cortex-A72 del CM4 no cuenta con extensiones DOTPROD, I8MM ni SVE, pero sí con FMA (Fused Multiply-Add) que acelera las operaciones de matriz. El rendimiento observado de ~3.6 t/s en generación para modelos Q4_K_M de ~1.5B parámetros es adecuado para aplicaciones de chat interactivo y consultas SQL parametrizadas.

---

## 9. Archivo de Configuración — config.yaml

### Estado: ✅ COMPLETADO

El archivo `config.yaml` es generado automáticamente por SIP-Edge en el primer arranque con valores por defecto para el EdgeBox-RPI-200. Se encuentra en `/home/sipedge/sip_edge/config.yaml`.

### Contenido actual:

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
```

| Sección | Parámetro | Valor | Descripción |
|---------|-----------|-------|-------------|
| `rs485` | `path` | `/dev/ttyACM0` | Puerto de la báscula |
| `rs485` | `baudrate` | `115200` | Velocidad serial |
| `rs485` | `parity` | `N` | Sin paridad |
| `rs485` | `data_bits` | `8` | 8 bits de datos |
| `rs485` | `stop_bits` | `1.0` | 1 bit de parada |
| `rs232` | `path` | `/dev/ttyACM1` | Puerto del PC externo |
| `rs232` | `baudrate` | `115200` | Velocidad serial |
| `gsm` | `modem_index` | `0` | Índice en ModemManager |
| `scale` | `timeout_seconds` | `3` | Timeout de respuesta de báscula |
| `session` | `session_timeout_minutes` | `15` | Bloqueo por inactividad |

---

## 10. Servicios del Sistema

### Estado actual:

| Servicio | Estado | Auto-start | Función |
|----------|--------|------------|---------|
| `mariadb.service` | ✅ Active | ✅ Enabled | Base de datos MariaDB 11.8.6 |
| `sip-edge.service` | ✅ Active | ✅ Enabled | Backend SIP-Edge (FastAPI + uvicorn) |
| `ModemManager.service` | ✅ Active | — | Gestión del módem 4G Quectel EC25 |
| `NetworkManager.service` | ✅ Active | — | Gestión de conexiones de red |
| `ssh.service` | ✅ Active | — | Acceso SSH remoto |
| `cron.service` | ✅ Active | — | Tareas programadas |
| `systemd-timesyncd.service` | ✅ Active | — | Sincronización NTP |
| `save-hwclock.service` | ✅ Active | — | Persistencia del RTC PCF8563 |
| `quectel-init.service` | ✅ Active | — | Inicialización del módem al arranque |

### Dependencias entre servicios:

```
mariadb.service ─────┐
network.target ──────┤
                     ├──→ sip-edge.service
                     │
ModemManager.service ┘
```

---

## 11. Resumen de Archivos Configurados

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `/boot/firmware/config.txt` | Overlays RTC, I2C, UART, GPIO | ✅ Informe 01 |
| `/etc/systemd/system/save-hwclock.service` | Sincronización RTC | ✅ Informe 01 |
| `/etc/NetworkManager/system-connections/Quectel-4G.nmconnection` | Conexión 4G | ✅ Informe 01 |
| `/usr/local/bin/quectel-init.sh` | Inicialización módem | ✅ Informe 01 |
| `/etc/systemd/system/quectel-init.service` | Servicio inicialización módem | ✅ Informe 01 |
| `/usr/local/bin/switch_network.sh` | Conmutación de red (eth/4g/dual) | ✅ Informe 01 |
| `/usr/local/bin/send_sms.sh` | Envío de SMS de prueba | ✅ Informe 01 |
| `/etc/lightdm/lightdm.conf` | Auto-login modo kiosco | ✅ Informe 01 |
| `/etc/polkit-1/localauthority/50-local.d/10-modemmanager.pkla` | Permisos PolicyKit módem | ✅ Informe 02 |
| `/etc/systemd/system/sip-edge.service` | Servicio SIP-Edge | ✅ Informe 02 |
| `/home/sipedge/sip_edge/.env` | Variables de entorno SIP-Edge | ✅ Informe 02 |
| `/home/sipedge/sip_edge/config.yaml` | Configuración de hardware y sesión | ✅ Informe 02 |
| `/usr/local/bin/llama-*` | Binarios llama.cpp v9632 (49 herramientas) | ✅ Informe 02 |
| `/home/models/*.gguf` | Modelos GGUF para inferencia (3 modelos, ~4.9 GB) | ✅ Informe 02 |

---

## 12. Conclusión

El entorno de ejecución del EdgeBox-RPI-200 está **completamente configurado y operativo**. Todos los componentes de software necesarios para el funcionamiento de SIP-Edge están instalados, configurados y verificados:

- **Sistema operativo** Debian 13 aarch64 con kernel 6.12, aprovechando los 8 GB de RAM.
- **Base de datos** MariaDB 11.8 con la base `sip_edge` y el usuario de aplicación creados.
- **Aplicación SIP-Edge** ejecutándose como servicio systemd con auto-inicio, exponiendo 15 endpoints REST en el puerto 8000.
- **Motor de inferencia llama.cpp** v8763 con 42 herramientas instaladas globalmente y 3 modelos GGUF descargados (~4.9 GB total).
- **Hardware industrial** (RS485, RS232, RTC, módem 4G) detectado y accesible desde el usuario `sipedge`.
- **Red** Ethernet activa (192.168.1.42), módem 4G configurado (pendiente plan de datos).

El sistema está listo para desarrollo y pruebas de las features pendientes: SMS Service (#7), AI Agent (#8), RS232 Transmission (#11), Emergency Mode (#9), Password Reset SMS (#12), y Backup System (#10).

---

