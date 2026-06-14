
---

## Informe de Progreso 1: Configuracion de Hardware — EdgeBox-RPI-200

> **Alcance:** Sistema operativo base, usuarios, grupos, perifericos de hardware, scripts de gestion de hardware, watchdog.

---

### 1. Migracion del Sistema Operativo

**Estado: COMPLETADO**

Migracion del sistema base(Debian 12 Bookworm) a una version nueva de 64-bit puro para habilitar modelos LLM > 4GB, sin modificar el hardware industrial.

| Paso | Detalle |
|------|---------|
| **Diagnostico** | Kernel `aarch64`, userland 32-bit → 8 GB RAM no aprovechados por proceso |
| **Arranque Live-USB** | `BOOT_ORDER=0xf21546` en EEPROM → pendrive sin desarmar el chasis |
| **Flasheo eMMC** | `rpi-clone` (no `dd`) → formateo correcto de eMMC + `PARTUUID` de arranque |
| **SO Instalado** | Raspberry Pi OS 64-bit (Debian 13 (Trixie) + kernel 6.12.) |
| **Arquitectura** | `getconf LONG_BIT` = 64 → 8 GB RAM totales liberados |
| **Respaldo udev** | Reglas `99-quectel-ttyUSB2-blacklist.rules` y `/etc/rc.local` preservadas |

---

### 2. Usuarios del Sistema y Permisos - Estado: COMPLETADO

### 2.1 Usuario administrador

| Campo | Valor |
|-------|-------|
| **Host** | SIP-Edge |
| **Usuario** | `admin` |
| **Contrasena** | `inasc1234` |

### 2.2 Usuario de aplicacion

```bash
sudo adduser sipedge
# Full Name: Analista de Pesaje Materia Extrana
# Password: sipedge1234
```

| Campo | Valor |
|-------|-------|
| **Usuario** | `sipedge` |
| **Contrasena** | `sipedge1234` |
| **SSH** | `ssh sipedge@192.168.1.28` (IP inicial) |

### 2.3 Grupos para acceso a perifericos

```bash
sudo usermod -a -G dialout sipedge   # Puertos serie /dev/ttyACM*
sudo usermod -a -G video sipedge     # Aceleracion grafica (DRM, framebuffer)
sudo usermod -a -G i2c sipedge       # Bus I2C (RTC, sensores)
sudo usermod -a -G gpio sipedge      # Control de pines GPIO
sudo usermod -a -G tty sipedge       # Acceso general a terminales
sudo usermod -a -G plugdev sipedge   # Dispositivos USB (modem 4G)
```

| Grupo | Proposito |
|-------|-----------|
| `dialout` | Acceso a puertos seriales `/dev/ttyACM*` |
| `video` | Aceleracion grafica (DRM, framebuffer) |
| `i2c` | Bus I2C (RTC PCF8563, sensores) |
| `gpio` | Control de pines GPIO |
| `tty` | Acceso general a terminales |
| `plugdev` | Dispositivos USB (modem 4G) |

### 2.4 Usuario de backup (bkmngr)

Usuario dedicado para la ejecucion del script de respaldo de base de datos via cron.
El script `scripts/backup.py` ejecuta `mysqldump` contra MariaDB y comprime el volcado
en `/home/bkmngr/backups/`, con rotacion FIFO de 30 dias y copia a USB con verificacion
CRC32.

| Campo | Valor |
|-------|-------|
| **Usuario** | `bkmngr` |
| **Contrasena** | `bkmngr1234` |
| **Home** | `/home/bkmngr` |
| **Directorio de backups** | `/home/bkmngr/backups/` |
| **Grupos** | `dialout` (acceso a puertos USB para exportacion) |
| **Shell** | `/bin/bash` |
| **sudo** | No |

```bash
sudo adduser bkmngr
# Full Name: Backup Operator
# Password: bkmngr1234
sudo usermod -a -G dialout bkmngr   # Acceso a USB para exportacion
sudo mkdir -p /home/bkmngr/backups
sudo chown bkmngr:bkmngr /home/bkmngr/backups
```

### 2.5 Auto-login modo kiosco

Archivo `/etc/lightdm/lightdm.conf`:

```ini
[Seat:*]
autologin-user=sipedge
autologin-user-timeout=0
```

Al encender el equipo, inicia sesion automaticamente con `sipedge` y lanza
la interfaz grafica sin intervencion.

---

## 3. Perifericos de Hardware

### 3.1 RTC (Reloj de Tiempo Real) PCF8563 - Estado: COMPLETADO

| Componente | Estado | Detalle |
|------------|--------|---------|
| Overlay en config.txt | Activo | `dtoverlay=i2c-rtc,pcf8563` |
| Deteccion por kernel | Activo | Registrado como `rtc0` |
| Comando hwclock | Instalado | Lectura/escritura correcta |
| Sincronizacion hora | Activo | Lectura/escritura correcta |
| Servicio systemd | Activo | `save-hwclock.service` |

**Comandos de verificacion:**

```bash
sudo hwclock -r          # Lee hora del RTC
sudo hwclock -w          # Guarda hora del sistema en RTC
timedatectl status       # Verifica estado general
```

**Archivos modificados:**
- `/boot/firmware/config.txt` — Overlay del RTC
- `/etc/systemd/system/save-hwclock.service` — Servicio de sincronizacion

**Observaciones:**
- El RTC funciona correctamente y mantiene la hora entre reinicios
- El servicio guarda automaticamente la hora al apagar el sistema

---

### 3.2 Modulo 4G LTE Quectel EC25 - Estado: COMPLETADO 

Opcional pendiente: plan de datos activo

#### Configuracion realizada

| Componente | Estado | Detalle |
|------------|--------|---------|
| Deteccion USB | OK | ID `2c7c:0125` |
| Drivers kernel | OK | `option`, `qmi_wwan` cargados |
| Puertos seriales | OK | `ttyUSB0`, `ttyUSB1`, `ttyUSB2`, `ttyUSB3` |
| Interfaz de red | OK | `wwan0` con IP asignada |
| ModemManager | OK | Detecta y gestiona el modem |
| Envio SMS | OK | Comandos AT funcionales |
| SIM card | OK | Tigo Colombia (operador 732103) |
| Senal LTE | OK | 89% (vs. 67% inicial con antena wifi) |
| Conexion de datos | OK | Bearer activo, IP `10.83.137.6` |
| APN configurado | OK | `internet.tigo.com.co` |
| NetworkManager | OK | Conexion "Quectel-4G" creada |

#### APN

| Parametro | Valor |
|-----------|-------|
| **APN** | `web.colombiamovil.com.co` |
| **Usuario** | (vacio) |
| **Contrasena** | (vacio) |
| **Autenticacion** | PAP |
| **Tipo APN** | default, supl |

#### Comandos de verificacion

```bash
mmcli -m 0                           # Estado del modem
mmcli -b 1                           # Estado del bearer
ip addr show wwan0                   # IP asignada
nmcli connection show Quectel-4G     # Configuracion de red 4G
```

#### Scripts de gestion de red

| Script | Funcion |
|--------|---------|
| `/usr/local/bin/switch_network.sh status` | Muestra estado de conexiones |
| `/usr/local/bin/switch_network.sh eth` | Activa solo Ethernet |
| `/usr/local/bin/switch_network.sh 4g` | Activa solo 4G |
| `/usr/local/bin/switch_network.sh dual` | Activa Ethernet + 4G |

#### Script de prueba SMS

```bash
sudo /usr/local/bin/send_sms.sh
```

#### Archivos modificados

- `/etc/NetworkManager/system-connections/Quectel-4G.nmconnection` — Conexion 4G
- `/usr/local/bin/quectel-init.sh` — Inicializacion del modem
- `/etc/systemd/system/quectel-init.service` — Servicio de inicializacion
- `/etc/polkit-1/localauthority/50-local.d/10-modemmanager.pkla` — Permisos PolicyKit

#### Observaciones

- El modem funciona correctamente a nivel de hardware
- La conexion a internet requiere plan de datos activo en la SIM
- Envio de SMS activo y configurado
- **Pendiente:** Registrar IMEI `862708046475815` en Tigo (15 dias)

---

### 3.3 Puertos Industriales RS232 / RS485  - Estado: COMPLETADO 


#### Mapeo de puertos

| Puerto fisico | Dispositivo | Proposito |
|---------------|-------------|-----------|
| RS485 | `/dev/ttyACM0` | Comunicacion con bascula DINI ARGEO DFWLI-2 |
| RS232 | `/dev/ttyACM1` | Transmision de datos a PC externo |

#### Verificacion de dispositivos

```bash
ls -la /dev/ttyACM*
# crw-rw---- 1 root dialout 166, 0 Apr  5 17:31 /dev/ttyACM0
# crw-rw---- 1 root dialout 166, 1 Apr  5 17:31 /dev/ttyACM1
```

Los puertos pertenecen a `root:dialout`. El usuario `sipedge` esta en el grupo
`dialout`, por lo que tiene acceso de lectura/escritura sin `sudo`.

#### Configuracion de parametros seriales

```bash
# RS232 a 115200 baud, 8 bits datos, sin paridad, 1 bit parada
stty -F /dev/ttyACM1 115200 cs8 -cstopb -parenb -echo
```

| Parametro | Valor | Significado |
|-----------|-------|-------------|
| `115200` | Velocidad | 115200 baudios |
| `cs8` | 8 bits | 8 bits de datos |
| `-cstopb` | 1 bit | 1 bit de parada |
| `-parenb` | Sin paridad | Sin bit de paridad |
| `-echo` | Sin eco | Desactiva eco local |

#### Prueba de comunicacion

```bash
# Instalar putty para pruebas interactivas
sudo apt install putty

# Prueba rapida con echo/cat
echo "Hola desde EdgeBox" > /dev/ttyACM1
```

#### Puertos adicionales del modem 4G

| Dispositivo | Funcion |
|-------------|---------|
| `/dev/ttyUSB0` | Puerto QMI (ignorado por ModemManager) |
| `/dev/ttyUSB1` | GPS NMEA |
| `/dev/ttyUSB2` | Comandos AT |
| `/dev/ttyUSB3` | Comandos AT |

---

### 3.4 Hardware Watchdog (WDT) — BCM2711  - Estado: COMPLETADO 

El watchdog del SoC BCM2711 (modulo `bcm2835_wdt`, compilado como `builtin`
en el kernel) fue detectado activo desde la instalacion del sistema.
Raspberry Pi OS incluye un drop-in en
`/usr/lib/systemd/system.conf.d/40-rpi-enable-watchdog.conf` que lo habilita
con un timeout por defecto de **1 minuto**.
Se redujo el timeout de 1 minuto a 30 segundos para cumplir `[RNF-003]`.

#### Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `/boot/firmware/config.txt` | Agregado `dtparam=watchdog=on` |
| `/etc/systemd/system.conf` | `#RuntimeWatchdogSec=off` → `RuntimeWatchdogSec=30` |
| `/etc/systemd/system.conf.d/50-watchdog-30s.conf` | **Nuevo** — sobreescribe default RPi OS (1min → 30s) |
| `/etc/systemd/system/sip-edge.service` | Agregado `WatchdogSec=30` en `[Service]` |

#### Backups creados (`20260614_134638`)

- `/boot/firmware/config.txt.bak.20260614_134638`
- `/etc/systemd/system.conf.bak.20260614_134638`
- `/etc/systemd/system/sip-edge.service.bak.20260614_134638`

#### Verificacion

```bash
dmesg | grep -i watchdog
# systemd[1]: Watchdog running with a hardware timeout of 30s.

systemctl show -p RuntimeWatchdogUSec
# RuntimeWatchdogUSec=30s

ls -la /dev/watchdog*
# crw------- 1 root root 10, 130 Jun 14 13:50 /dev/watchdog
# crw------- 1 root root 248, 0 Jun 14 13:50 /dev/watchdog0
```

#### Documentacion detallada

Ver `docs/Configuracion del Hardware Watchdog.md` para el procedimiento
completo, plan de rollback (opciones A y B), y restauracion desde backups.

---

### 3.5 UPS (Opcional — No instalada) - Estado: NO DISPONIBLE

La UPS es un accesorio opcional del EdgeBox-RPI-200 que **no esta instalada**
en este dispositivo.

#### Lo que se intento configurar

| Componente | Estado | Nota |
|------------|--------|------|
| Overlay gpio-shutdown | Configurado | `dtoverlay=gpio-shutdown,gpio_pin=22,active_low=1,gpio_pull=up` |
| Deteccion de alarma | Presente | Dispositivo `soc:shutdown_button@16` detectado |
| Apagado automatico | No funciona | El sistema se apaga instantaneamente al perder AC |

#### Causa

El hardware de UPS (supercapacitor CXP-3R0306R y controlador LTC4041) no esta
presente, por lo que no hay almacenamiento de energia para mantener el sistema
durante un apagado controlado.

#### Accion recomendada

Eliminar el overlay de `config.txt` para evitar comportamientos inesperados,
o adquirir el modulo UPS opcional si se necesita la funcionalidad.

```bash
# Comentar la linea en config.txt:
# dtoverlay=gpio-shutdown,gpio_pin=22,active_low=1,gpio_pull=up
sudo reboot
```

---

## 4. Servicios del Sistema (Hardware)

| Servicio | Estado | Funcion |
|----------|--------|---------|
| `save-hwclock.service` | Activo | Guarda hora en RTC al apagar |
| `ModemManager.service` | Activo | Gestiona el modem 4G |
| `NetworkManager.service` | Activo | Gestiona conexiones de red |
| `quectel-init.service` | Activo | Inicializa el modem al arranque |
| `ups-monitor.service` | No creado | No necesario (UPS ausente) |

---

## 5. Resumen de Archivos Configurados

| Archivo | Proposito | Estado |
|---------|-----------|--------|
| `/boot/firmware/config.txt` | Overlays RTC, I2C, UART, GPIO, WDT | Configurado |
| `/etc/systemd/system/save-hwclock.service` | Sincronizacion RTC | Creado |
| `/etc/NetworkManager/system-connections/Quectel-4G.nmconnection` | Conexion 4G | Creado |
| `/usr/local/bin/quectel-init.sh` | Inicializacion modem | Creado |
| `/etc/systemd/system/quectel-init.service` | Servicio inicializacion modem | Creado |
| `/usr/local/bin/switch_network.sh` | Conmutacion de red (eth/4g/dual) | Creado |
| `/usr/local/bin/send_sms.sh` | Envio de SMS de prueba | Creado |
| `/etc/lightdm/lightdm.conf` | Auto-login modo kiosco | Modificado |
| `/etc/polkit-1/localauthority/50-local.d/10-modemmanager.pkla` | Permisos PolicyKit modem | Creado |
| `/etc/systemd/system.conf` | RuntimeWatchdogSec=30 | Modificado (2026-06-14) |
| `/etc/systemd/system.conf.d/50-watchdog-30s.conf` | Override WDT 30s (RNF-003) | Creado (2026-06-14) |
| `/etc/systemd/system/sip-edge.service` | WatchdogSec=30 | Modificado (2026-06-14) |

---

## 6. Conclusion

El hardware del EdgeBox-RPI-200 tiene todos los perifericos esenciales
completamente configurados y verificados: RTC, modem 4G LTE, puertos
RS232/RS485, y watchdog de hardware a 30s cumpliendo `[RNF-003]`.

Los componentes de software (aplicacion SIP-Edge, MariaDB, Python, llama.cpp,
config.yaml) estan documentados en el **Informe 02 — Configuracion del Entorno
de Ejecucion**.

---
