# Manual de Instalacion — SIP-Edge en EdgeBox-RPI-200

> **Proposito:** Guia paso a paso para instalar SIP-Edge desde cero en un EdgeBox-RPI-200 nuevo.
> **Hardware objetivo:** SeeedStudio EdgeBox-RPI-200 (Raspberry Pi CM4, 8 GB RAM, 32 GB eMMC).
> **Tiempo estimado:** 3-4 horas (dependiendo de velocidad de descarga y compilacion).

---

## Indice

1. [Preparacion del Hardware](#1-preparacion-del-hardware)
2. [Sistema Operativo](#2-sistema-operativo)
3. [Usuarios y Permisos](#3-usuarios-y-permisos)
4. [Red y Conectividad](#4-red-y-conectividad)
5. [Perifericos de Hardware](#5-perifericos-de-hardware)
6. [Base de Datos — MariaDB](#6-base-de-datos-mariadb)
7. [Python y Dependencias](#7-python-y-dependencias)
8. [llama.cpp — Motor de Inferencia LLM](#8-llamacpp-motor-de-inferencia-llm)
9. [Despliegue de la Aplicacion](#9-despliegue-de-la-aplicacion)
10. [Base de Datos — Migraciones y Seeds](#10-base-de-datos-migraciones-y-seeds)
11. [Servicio systemd](#11-servicio-systemd)
12. [Modo Kiosco](#12-modo-kiosco)
13. [Permisos sudo para mmcli (CRITICO)](#13-permisos-sudo-para-mmcli-critico)
14. [Configuracion Post-Instalacion](#14-configuracion-post-instalacion)
15. [Verificacion Final](#15-verificacion-final)
16. [Troubleshooting](#16-troubleshooting)
17. [Referencia Rapida](#17-referencia-rapida)

---

## 1. Preparacion del Hardware

### 1.1 Material necesario

| Item | Cantidad | Notas |
|------|----------|-------|
| EdgeBox-RPI-200 | 1 | Con fuente de alimentacion 12-24V DC |
| Pendrive USB | 1 | Minimo 16 GB, para flashear el SO |
| Teclado USB | 1 | Para configuracion inicial |
| Mouse USB | 1 | |
| Monitor HDMI | 1 | Solo durante instalacion |
| Cable Ethernet | 1 | Conexion a red local |
| SIM Tigo Colombia | 1 | Para modulo 4G Quectel EC25 |
| Antena 4G LTE | 1 | Conexion al puerto SMA del modem |

### 1.2 Insertar SIM y antena

1. Localizar la ranura SIM en el lateral del EdgeBox.
2. Insertar la SIM con el contacto dorado hacia abajo.
3. Conectar la antena 4G al puerto SMA marcado como `WWAN` o `4G`.

### 1.3 Conexiones fisicas

```
[EdgeBox]──HDMI──[Monitor]
[EdgeBox]──USB──[Teclado + Mouse]
[EdgeBox]──Ethernet──[Router/Switch LAN]
[EdgeBox]──DC 12-24V──[Fuente de alimentacion]
```

---

## 2. Sistema Operativo

### 2.1 Instalar Raspberry Pi OS 64-bit en la eMMC

> **Importante:** El EdgeBox usa almacenamiento eMMC interno, NO tarjeta SD.
> No se puede extraer la CM4 para flashearla en otro dispositivo sin desarmar el chasis.
> El metodo usado en produccion evita `rpiboot` y `dd`, usando en su lugar arranque
> desde USB live + clonacion con `rpi-clone`.

#### Paso A — Preparar el pendrive USB booteable

En otro PC con Linux:

```bash
# 1. Descargar Raspberry Pi OS 64-bit (Debian 13 Trixie)
# 2. Flashear la imagen en un pendrive USB (minimo 16 GB)
#    usando Raspberry Pi Imager o dd:
sudo dd if=2025-11-19-raspios-trixie-arm64.img of=/dev/sdX bs=4M status=progress

# 3. (Opcional) Pre-configurar hostname, usuario y SSH
#    - Montar la particion boot del pendrive
#    - Crear archivo ssh vacio: touch /media/boot/ssh
#    - Crear userconf.txt con credenciales iniciales
```

#### Paso B — Forzar arranque desde USB en el EdgeBox

```bash
# En el EdgeBox (con SO actual), configurar la EEPROM para priorizar USB:
sudo rpi-eeprom-config -e
# Cambiar BOOT_ORDER a: 0xf21546
#   0xf2 = USB primero
#   0x15 = SD card
#   0x46 = eMMC (ultimo recurso)
# Guardar y salir.

# Alternativa: editar directamente
# sudo nano /boot/firmware/config.txt
# Agregar: program_boot_order=0xf21546
```

Apagar el EdgeBox, conectar el pendrive USB preparado, y encender. El sistema arrancara desde el pendrive.

> **Ventaja de este metodo:** No requiere desarmar el chasis ni extraer la CM4 a una
> placa portadora (Carrier Board).

#### Paso C — Clonar el USB a la eMMC con rpi-clone

Una vez arrancado desde el pendrive USB:

```bash
# 1. Instalar rpi-clone
sudo apt update
sudo apt install -y rpi-clone

# 2. Identificar dispositivos
lsblk
# mmcblk0 = eMMC interna (destino, ~29 GB)
# sda     = pendrive USB (origen, ~16 GB)

# 3. Clonar el sistema de archivos del USB a la eMMC
sudo rpi-clone mmcblk0

# rpi-clone hace lo siguiente automaticamente:
#   - Formatea correctamente la eMMC (evitando corrupcion por diferencia de tamaños)
#   - Copia el sistema de archivos sector a sector
#   - Reescribe los PARTUUID de arranque en la eMMC
#   - Ajusta el tamaño de la particion root para usar todo el espacio disponible
```

> **Por que rpi-clone y no dd:**
> - `dd` copia el tamaño exacto del USB (ej. 16 GB) a la eMMC (32 GB), desperdiciando la mitad del espacio.
> - `dd` duplica los PARTUUID, causando conflictos si ambos dispositivos estan presentes.
> - `rpi-clone` resuelve ambos problemas: expande la particion y regenera PARTUUID unicos.

#### Paso D — Apagar, retirar USB, y verificar

```bash
sudo poweroff
```

1. Desconectar el pendrive USB
2. Encender el EdgeBox (arrancara desde eMMC)
3. Verificar:

```bash
# Confirmar que arranco desde eMMC
lsblk | grep mmcblk0
df -h /
# /dev/mmcblk0p2  29G  ...  (debe mostrar ~29 GB, no 16 GB)

getconf LONG_BIT
# 64

cat /etc/os-release | grep PRETTY_NAME
# PRETTY_NAME="Debian GNU/Linux 13 (trixie)"
```

### 2.2 Primer arranque — verificacion

```bash
# Conectar por SSH (desde PC en la misma red)
ssh admin@<ip-asignada-por-dhcp>

# Verificar arquitectura 64-bit
getconf LONG_BIT
# Debe devolver: 64

# Verificar RAM disponible
free -h | grep Mem
# Debe mostrar ~7.6 Gi

# Verificar SO
cat /etc/os-release | grep PRETTY_NAME
# PRETTY_NAME="Debian GNU/Linux 13 (trixie)"

# Verificar kernel
uname -m
# aarch64
```

### 2.3 Actualizar el sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.4 Configurar IP fija

```bash
# Editar /etc/network/interfaces.d/eth0 o usar nmcli
# en este ejemplo se asigna la ip: 192.18.1.42, asigne la que se ajuste a su necesidad.
sudo nmcli connection modify "Wired connection 1" \
  ipv4.addresses 192.168.1.42/24 \
  ipv4.gateway 192.168.1.1 \
  ipv4.dns "8.8.8.8 8.8.4.4" \
  ipv4.method manual

sudo nmcli connection up "Wired connection 1"
```

Verificar:
```bash
ip addr show eth0
# Debe mostrar: inet 192.168.1.42/24
```

---

## 3. Usuarios y Permisos

### 3.1 Crear usuario de aplicacion

```bash
sudo adduser sipedge
# Full Name: Analista de Pesaje Materia Extrana
# Password: sipedge1234
```

### 3.2 Crear usuario de backup

```bash
sudo adduser bkmngr
# Full Name: Backup Operator
# Password: bkmngr1234

sudo mkdir -p /home/bkmngr/backups
sudo chown bkmngr:bkmngr /home/bkmngr/backups
```

### 3.3 Asignar grupos al usuario sipedge

```bash
sudo usermod -a -G dialout sipedge   # Puertos seriales /dev/ttyACM*
sudo usermod -a -G video sipedge     # Aceleracion grafica
sudo usermod -a -G i2c sipedge       # Bus I2C (RTC)
sudo usermod -a -G gpio sipedge      # Pines GPIO
sudo usermod -a -G tty sipedge       # Terminales
sudo usermod -a -G plugdev sipedge   # Dispositivos USB (modem 4G)

# Verificar
groups sipedge
# sipedge : sipedge dialout video i2c gpio tty plugdev
```

### 3.4 Dar privilegios sudo a sipedge

```bash
sudo usermod -a -G sudo sipedge
```

### 3.5 Asignar grupos a bkmngr

```bash
sudo usermod -a -G dialout bkmngr   # Acceso a USB para exportacion
```

---

## 4. Red y Conectividad

### 4.1 Verificar interfaces

```bash
ip -br addr
# eth0    UP     192.168.1.42/24
# wwan0   DOWN   (aparece despues de configurar modem 4G)
# lo      UP     127.0.0.1/8
```

### 4.2 Modem 4G — Verificacion inicial

```bash
# Verificar que el modem es detectado por USB
lsusb | grep Quectel
# Bus 001 Device 003: ID 2c7c:0125 Quectel Wireless Solutions Co., Ltd. EC25 LTE modem

# Verificar puertos seriales del modem
ls -la /dev/ttyUSB*
# /dev/ttyUSB0  (QMI)
# /dev/ttyUSB1  (GPS NMEA)
# /dev/ttyUSB2  (Comandos AT)
# /dev/ttyUSB3  (Comandos AT)
```

### 4.3 Configurar APN

```bash
# Crear conexion 4G en NetworkManager
sudo nmcli connection add type gsm \
  con-name "Quectel-4G" \
  ifname wwan0 \
  apn internet.tigo.com.co \
  connection.autoconnect yes

# Verificar
nmcli connection show Quectel-4G
```

### 4.4 Verificar modem con mmcli

```bash
mmcli -m 0
# Debe mostrar: Quectel EC25, estado enabled, operador Tigo (732103)

# Verificar senal
mmcli -m 0 --signal-get
# RSSI: -67 dBm (89%)
```

### 4.5 Activar conexion de datos (si hay plan)

```bash
# Activar bearer (conexion de datos)
sudo mmcli -m 0 --simple-connect=apn=internet.tigo.com.co

# Verificar IP asignada
ip addr show wwan0
# inet 10.x.x.x
```

> **Nota:** El plan de datos 4G es opcional. Sin el, las funcionalidades que requieren internet
> (Telegram, descarga de modelos) no funcionan. El envio/recepcion de SMS SI funciona sin plan
> de datos activo.

---

## 5. Perifericos de Hardware

### 5.1 Puertos Seriales RS485 / RS232

#### Verificar dispositivos

```bash
ls -la /dev/ttyACM*
# crw-rw---- 1 root dialout 166, 0 ... /dev/ttyACM0  (RS485 - bascula)
# crw-rw---- 1 root dialout 166, 1 ... /dev/ttyACM1  (RS232 - PC externo)
```

Los puertos pertenecen a `root:dialout`. El usuario `sipedge` ya esta en el grupo `dialout`.

#### Probar comunicacion

```bash
# Configurar parametros
stty -F /dev/ttyACM1 115200 cs8 -cstopb -parenb -echo

# Prueba de envio
echo "Hola desde EdgeBox" > /dev/ttyACM1

# Prueba de recepcion (Ctrl+C para salir)
cat /dev/ttyACM1
```

### 5.2 RTC (Reloj de Tiempo Real) PCF8563

#### Verificar overlay en config.txt

```bash
grep pcf8563 /boot/firmware/config.txt
# dtoverlay=i2c-rtc,pcf8563
```

Si no existe, agregarlo:
```bash
echo "dtoverlay=i2c-rtc,pcf8563" | sudo tee -a /boot/firmware/config.txt
```

#### Verificar despues de reiniciar

```bash
sudo hwclock -r          # Leer hora del RTC
timedatectl status       # Verificar estado general

# Sincronizar hora del sistema al RTC
sudo hwclock -w
```

### 5.3 Hardware Watchdog (WDT)

El watchdog del SoC BCM2711 (`bcm2835_wdt`) viene habilitado por defecto en Raspberry Pi OS
con timeout de 1 minuto. Se recomienda reducirlo a 20 segundos.

#### Verificar estado actual

```bash
dmesg | grep -i watchdog
# bcm2835_wdt: Broadcom BCM2835 watchdog timer

systemctl show -p RuntimeWatchdogUSec
# RuntimeWatchdogUSec=1min

ls -la /dev/watchdog*
# crw------- 1 root root 10, 130 ... /dev/watchdog
# crw------- 1 root root 248, 0 ... /dev/watchdog0
```

#### Reducir timeout a 30s (recomendado)

```bash
# Crear drop-in que sobreescribe el default de 1min
echo "[Manager]
RuntimeWatchdogSec=20" | sudo tee /etc/systemd/system.conf.d/50-watchdog-20s.conf

# Recargar systemd
sudo systemctl daemon-reload
sudo reboot
```

Verificar despues del reinicio:
```bash
systemctl show -p RuntimeWatchdogUSec
# RuntimeWatchdogUSec=30s
```

> **Documentacion detallada:** `docs/Configuracion del Hardware Watchdog.md`

---

## 6. Base de Datos — MariaDB

### 6.1 Instalacion

```bash
sudo apt install -y mariadb-server
sudo systemctl enable --now mariadb

# Verificar
sudo systemctl status mariadb
# Active: active (running)
```

### 6.2 Crear base de datos y usuario

```bash
sudo mysql <<SQL
CREATE DATABASE IF NOT EXISTS sip_edge CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'sip_user'@'localhost' IDENTIFIED BY 'sip_pass';
GRANT ALL PRIVILEGES ON sip_edge.* TO 'sip_user'@'localhost';
FLUSH PRIVILEGES;
SQL
```

### 6.3 Verificar acceso

```bash
mysql -u sip_user -psip_pass sip_edge -e "SELECT 1 AS test;"
# +------+
# | test |
# +------+
# |    1 |
# +------+
```

### 6.4 Configurar backup cron (bkmngr)

```bash
# Agregar tarea cron para backup diario
sudo crontab -u bkmngr -e
# Agregar la linea:
# 55 23 * * * cd /home/sipedge/sip_edge && /home/sipedge/sip_edge/venv/bin/python scripts/backup.py >> /var/log/sip_edge_backup.log 2>&1
```

---

## 7. Python y Dependencias

### 7.1 Verificar Python del sistema

```bash
python3 --version
# Python 3.13.x
```

### 7.2 Clonar repositorio

```bash
# Como usuario sipedge
su - sipedge

git clone https://github.com/rojecas/sip_edge.git /home/sipedge/sip_edge
cd /home/sipedge/sip_edge
```

### 7.3 Crear entorno virtual e instalar dependencias

```bash
cd /home/sipedge/sip_edge
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 7.4 Verificar instalacion

```bash
source /home/sipedge/sip_edge/venv/bin/activate
python -c "import fastapi, sqlalchemy, pydantic, serial, yaml; print('OK')"
# OK
```

---

## 8. llama.cpp — Motor de Inferencia LLM

### 8.1 Instalar dependencias de compilacion

```bash
sudo apt install -y git build-essential cmake libssl-dev
```

### 8.2 Compilar llama.cpp

```bash
cd /tmp
git clone --depth 1 https://github.com/ggerganov/llama.cpp llama.cpp_build
cd llama.cpp_build
mkdir build && cd build

# Compilar (-j1 recomendado para CM4: 4 cores, RAM limitada)
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release -j1

# Instalar binarios
sudo cp bin/* /usr/local/bin/

# Verificar
llama-cli --version
# version: 1 (xxxx)
# built with GNU xx for Linux aarch64
```

### 8.3 Descargar modelos

```bash
sudo mkdir -p /home/models
sudo chown sipedge:sipedge /home/models

# Qwen 2.5 1.5B (recomendado para produccion, ~1.1 GB)
wget -O /home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf

# Opcional: Gemma 4 2B (~2.9 GB)
# wget -O /home/models/gemma-4-E2B-it-Q4_K_M.gguf \
#   <url>

# Verificar
ls -lh /home/models/
# qwen2.5-1.5b-instruct-q4_k_m.gguf  1.1 GB
```

### 8.4 Crear servicio systemd para llama-server

```bash
sudo tee /etc/systemd/system/llama-server.service << 'EOF'
[Unit]
Description=llama.cpp Server (LLM Inference)
After=network.target

[Service]
Type=simple
User=sipedge
ExecStart=/usr/local/bin/llama-server \
  -m /home/models/qwen2.5-1.5b-instruct-q4_k_m.gguf \
  -c 4096 \
  --host 127.0.0.1 \
  --port 8080
Restart=always
RestartSec=10

# CPU pinning: cores 0-2 para LLM, core 3 libre para backend
CPUAffinity=0-2

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now llama-server

# Verificar
curl http://127.0.0.1:8080/health
# {"status": "ok"}
```

---

## 9. Despliegue de la Aplicacion

### 9.1 Archivo .env

```bash
cd /home/sipedge/sip_edge

tee .env << 'EOF'
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=sip_edge
DB_USER=sip_user
DB_PASSWORD=sip_pass
JWT_SECRET_KEY=sip_edge_jwt_secret_prod
ADMIN_DEFAULT_PASSWORD=admin
DEV_MODE=false
AI_PRIMARY_BACKEND=local
EOF
```

| Variable | Valor | Descripcion |
|----------|-------|-------------|
| `DB_HOST` | 127.0.0.1 | MariaDB en localhost |
| `DB_NAME` | sip_edge | Nombre de la BD |
| `DB_USER` | sip_user | Usuario de BD |
| `DB_PASSWORD` | sip_pass | Password de BD |
| `JWT_SECRET_KEY` | (valor unico) | Clave para firmar tokens JWT. **Cambiar en produccion.** |
| `ADMIN_DEFAULT_PASSWORD` | admin | Password inicial del admin (cambiar en primer login) |
| `DEV_MODE` | false | Hardware real activo (RS232/RS485/GSM) |
| `AI_PRIMARY_BACKEND` | local | `local` = llama.cpp, `remote` = DeepSeek API |

### 9.2 Archivo config.yaml

El archivo `config.yaml` se genera automaticamente en el primer arranque de la aplicacion.
No es necesario crearlo manualmente. Si se desea pre-configurar, copiar esta base:

```yaml
rs485:
  path: /dev/ttyACM0
  baudrate: 9600
  data_bits: 8
  parity: N
  stop_bits: 1.0
rs232:
  path: /dev/ttyACM1
  baudrate: 9600
  data_bits: 8
  parity: N
  stop_bits: 1.0
gsm:
  modem_index: 0
scale:
  timeout_seconds: 3
session:
  session_timeout_minutes: 240
```

### 9.3 Iniciar la aplicacion manualmente (prueba)

```bash
cd /home/sipedge/sip_edge
source venv/bin/activate

# Ejecutar en primer plano para ver logs
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Verificar en otra terminal
curl http://127.0.0.1:8000/health
# {"status": "ok"}

# Ctrl+C para detener
```

---

## 10. Base de Datos — Migraciones y Seeds

### 10.1 Ejecutar migraciones

Las migraciones se ejecutan automaticamente al iniciar la aplicacion (via SQLAlchemy `create_all`).
Para migraciones manuales (archivos `.sql`), ejecutar en orden cronologico:

```bash
cd /home/sipedge/sip_edge

# Listar migraciones SQL pendientes
ls -1 database/migrations/*.sql

# Ejecutar cada migracion en orden
for f in database/migrations/*.sql; do
  echo "Ejecutando: $f"
  mysql -u sip_user -psip_pass sip_edge < "$f"
done
```

> **Nota:** Las migraciones `.py` se ejecutan automaticamente por los modelos SQLAlchemy.
> Las migraciones `.sql` contienen cambios de schema que SQLAlchemy no detecta
> (ej: ENUM modifications, indices compuestos).

### 10.2 Verificar tablas creadas

```bash
mysql -u sip_user -psip_pass sip_edge -e "SHOW TABLES;"
```

Tablas esperadas:
```
users
haciendas
suertes
weighings
emergency_mode_log
report_templates
report_template_users
anomaly_log
backup_logs
sms_conversations
sms_messages
sms_ai_tool_log
```

### 10.3 Ejecutar seeds (datos iniciales)

```bash
cd /home/sipedge/sip_edge
source venv/bin/activate

# Seed de datos de prueba (opcional, solo para desarrollo)
python database/seeds/seed_all.py
```

### 10.4 Verificar usuario admin inicial

```bash
mysql -u sip_user -psip_pass sip_edge -e "SELECT id, username, role FROM users;"
# Debe mostrar al menos 1 usuario admin (creado en el primer arranque)
```

---

## 11. Servicio systemd

### 11.1 Crear archivo de unidad

```bash
sudo tee /etc/systemd/system/sip-edge.service << 'EOF'
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
EOF
```

> `WatchdogSec=20` integra el servicio con el hardware watchdog del sistema.
> Si el proceso se congela por mas de 20s, systemd lo reinicia automaticamente.

### 11.2 Activar el servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable sip-edge.service
sudo systemctl start sip-edge.service

# Verificar
sudo systemctl status sip-edge
# Active: active (running)

# Logs
sudo journalctl -u sip-edge -f
```

---

## 12. Modo Kiosco

### 12.1 Auto-login (LightDM)

```bash
sudo tee -a /etc/lightdm/lightdm.conf << 'EOF'

[Seat:*]
autologin-user=sipedge
autologin-user-timeout=0
EOF
```

### 12.2 Instalar Chromium

```bash
sudo apt install -y chromium-browser
```

### 12.3 Configurar autostart de Chromium en modo kiosco

Crear archivo de autostart para el usuario `sipedge`:

```bash
mkdir -p /home/sipedge/.config/autostart

tee /home/sipedge/.config/autostart/kiosk.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=SIP-Edge Kiosk
Exec=chromium-browser --kiosk --noerrdialogs --disable-infobars --disable-session-crashed-bubble --disable-restore-session-state http://127.0.0.1:8000
X-GNOME-Autostart-enabled=true
EOF

chown -R sipedge:sipedge /home/sipedge/.config
```

### 12.4 Deshabilitar screen saver y power management

```bash
# Como usuario sipedge
su - sipedge

mkdir -p /home/sipedge/.config/lxsession/LXDE-pi
tee /home/sipedge/.config/lxsession/LXDE-pi/autostart << 'EOF'
@xset s off
@xset -dpms
@xset s noblank
EOF
```

---

## 13. Permisos sudo para mmcli (CRITICO)

> **ATENCION:** Si este paso se omite, el envio y recepcion de SMS fallara
> silenciosamente. Los comandos de emergencia, reset de password y consultas
> AI via SMS no funcionaran.

```bash
echo 'sipedge ALL=(root) NOPASSWD: /usr/bin/mmcli *' | sudo tee /etc/sudoers.d/sip-edge
sudo chmod 440 /etc/sudoers.d/sip-edge
```

Verificar:
```bash
# Debe ejecutarse sin pedir password
sudo -n mmcli -m 0 --messaging-list-sms
# Respuesta esperada: "No sms messages were found" (o lista de SMS)
```

---

## 14. Configuracion Post-Instalacion

Una vez el sistema esta corriendo, completar la configuracion desde la interfaz web:

### 14.1 Acceder al sistema

1. Abrir navegador en `http://192.168.1.42:8000`
2. Iniciar sesion con:
   - Usuario: `admin`
   - Password: `admin` (cambiar inmediatamente)

### 14.2 Cambiar password del admin

1. Navegar a **Admin > Usuarios**
2. Editar el usuario `admin`
3. Establecer nueva contraseña
4. Guardar

### 14.3 Crear operadores y corresponsales

1. **Admin > Usuarios > Nuevo Usuario**
2. Completar: Usuario, Contraseña, Nombre Completo, Codigo de Empresa, Telefono, Rol
3. Repetir para cada operador de laboratorio y corresponsal

Roles:
| Rol | Acceso |
|-----|--------|
| `admin` | Total: configuracion, usuarios, haciendas, suertes, reportes, backups |
| `operator` | Solo kiosko de pesaje e historial |
| `corresponsal` | Solo via SMS (recibe reportes, consulta datos) |

### 14.4 Configurar puertos

1. **Admin > Configuracion**
2. Verificar que RS485 apunta a `/dev/ttyACM0` y RS232 a `/dev/ttyACM1`
3. Probar conectividad con el boton **Test** en cada puerto
4. Guardar

### 14.5 Crear haciendas y suertes

1. **Admin > Haciendas > Nueva Hacienda**
2. Ingresar codigo y nombre
3. **Admin > Suertes > Nueva Suerte**
4. Seleccionar hacienda padre, ingresar codigo (max 4 caracteres)

### 14.6 Configurar reportes programados (opcional)

1. **Admin > Reportes > Nueva Plantilla**
2. Configurar: nombre, horarios, metricas deseadas, destinatarios SMS
3. Activar

### 14.7 Verificar envio de SMS

```bash
# Desde la EdgeBox
echo "57300XXXXXXX Prueba de SMS desde SIP-Edge" | sudo /usr/local/bin/send_sms.sh
```

O desde el panel admin, puede probar que el modem este conectado: **Admin > Configuracion > Test GSM**.

---

## 15. Verificacion Final

### 15.1 Smoke test — Health check

```bash
curl http://127.0.0.1:8000/health
# {"status": "ok"}
```

### 15.2 Estado de servicios

```bash
sudo systemctl status mariadb sip-edge llama-server
# Todos deben mostrar: active (running)
```

### 15.3 Puertos seriales

```bash
ls -la /dev/ttyACM*
# /dev/ttyACM0 (RS485)
# /dev/ttyACM1 (RS232)
```

### 15.4 Modem 4G

```bash
mmcli -m 0
# State: enabled
# 3GPP: Tigo Colombia (732103)
```

### 15.5 Watchdog

```bash
systemctl show -p RuntimeWatchdogUSec
# RuntimeWatchdogUSec=20s
```

### 15.6 LLM

```bash
curl http://127.0.0.1:8080/health
# {"status": "ok"}
```

### 15.7 Login y flujo de pesaje

1. Abrir `http://192.168.1.42:8000` en el navegador
2. Iniciar sesion como `admin`
3. Crear un usuario con rol operador
4. realizar el logout del administrador e ingresar con el nuevo usuario.
5. Navegar a Kiosko
6. Verificar que los campos de hacienda, suerte, tractomula, vagon y guia son accesibles
7. Verificar que la bascula responde (si esta conectada)

---

## 16. Troubleshooting

### 16.1 El servicio sip-edge falla al iniciar

```bash
# Ver logs
sudo journalctl -u sip-edge --no-pager -n 100

# Causas comunes:
# - MariaDB no esta corriendo: sudo systemctl start mariadb
# - Error de permisos en .env: ls -la /home/sipedge/sip_edge/.env (debe ser readable por sipedge)
# - Puerto 8000 ocupado: sudo lsof -i :8000
# - Dependencias faltantes: source venv/bin/activate && pip install -r requirements.txt
```

### 16.2 SMS no se envian/reciben

```bash
# Verificar permisos sudo mmcli (CRITICO)
sudo -n mmcli -m 0 --messaging-list-sms
# Si pide password: revisar Seccion 13

# Verificar modem
mmcli -m 0
# Si no aparece: sudo systemctl restart ModemManager

# Verificar SMSC
# Ver docs/Configuracion de SMSC para Quectel EC25.md
```

### 16.3 La bascula no responde

```bash
# Verificar que el puerto existe
ls -la /dev/ttyACM0

# Verificar permisos (sipedge debe estar en grupo dialout)
groups sipedge

# Probar comunicacion manual
stty -F /dev/ttyACM0 115200 cs8 -cstopb -parenb -echo
echo -ne "READ\r\n" > /dev/ttyACM0
cat /dev/ttyACM0 &
# Ctrl+C para salir
```

### 16.4 llama-server no inicia

```bash
# Ver logs
sudo journalctl -u llama-server --no-pager -n 50

# Causas comunes:
# - Modelo no encontrado: ls -la /home/models/
# - RAM insuficiente: free -h (necesita ~2 GB libres para Qwen 1.5B)
# - Error de compilacion: recompilar con -j1
```

### 16.5 Error "password is required" en mmcli

El archivo `/etc/sudoers.d/sip-edge` no existe o tiene error de sintaxis.
Revisar la Seccion 13 de este manual.

### 16.6 Watchdog reinicia el sistema cada 20s

Si el sistema se reinicia en ciclo, verificar:
```bash
# Ver si el watchdog esta activo
systemctl show -p RuntimeWatchdogUSec

# Desactivar temporalmente para diagnostico
sudo sed -i 's/^RuntimeWatchdogSec=20/#RuntimeWatchdogSec=0/' /etc/systemd/system.conf.d/50-watchdog-20s.conf
sudo reboot
```

---

## 17. Referencia Rapida

### Comandos de mantenimiento diario

```bash
# Estado del sistema
sudo systemctl status mariadb sip-edge llama-server

# Logs de la aplicacion
sudo journalctl -u sip-edge --no-pager -n 100

# Actualizar codigo
cd /home/sipedge/sip_edge && git pull && sudo systemctl restart sip-edge

# Backup manual
cd /home/sipedge/sip_edge && source venv/bin/activate && python scripts/backup.py

# Estado del modem
mmcli -m 0
```

### Credenciales por defecto

| Servicio | Usuario | Password |
|----------|---------|----------|
| SO (admin) | `admin` | `inasc1234` |
| SO (app) | `sipedge` | `sipedge1234` |
| SO (backup) | `bkmngr` | `bkmngr1234` |
| MariaDB | `sip_user` | `sip_pass` |
| SIP-Edge (web) | `admin` | `admin` (cambiar en primer login) |

### Puertos y servicios

| Servicio | Puerto | Acceso |
|----------|--------|--------|
| SIP-Edge API | 8000 | `http://192.168.1.42:8000` |
| llama-server | 8080 | `http://127.0.0.1:8080` |
| MariaDB | 3306 | `localhost` |
| SSH | 22 | `ssh sipedge@192.168.1.42` |

### Archivos clave

| Archivo | Proposito |
|---------|-----------|
| `/home/sipedge/sip_edge/.env` | Variables de entorno |
| `/home/sipedge/sip_edge/config.yaml` | Configuracion de puertos y session |
| `/etc/systemd/system/sip-edge.service` | Servicio systemd |
| `/etc/systemd/system/llama-server.service` | Servicio LLM |
| `/etc/sudoers.d/sip-edge` | Permisos sudo mmcli |
| `/etc/lightdm/lightdm.conf` | Auto-login kiosco |

---

*Manual de instalación. Rev 1.0 - 17-Jul-2026 - INASC SAS*
