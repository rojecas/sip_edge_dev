
---

## 📄 Informe de Progreso 1: Actualización y Configuración de Hardware Base **EdgeBox-RPI-200**

## 1. Avances Alcanzados (Completado ✅)

Se ha realizado exitosamente la migración del sistema base para habilitar la ejecución de modelos de Inteligencia Artificial (LLMs) superiores a 4GB, manteniendo intacta la integridad del hardware industrial.

*   **Diagnóstico de Sistema:** Se identificó que, aunque el Kernel era `aarch64`, el sistema de usuario (`userland`) era de 32 bits, lo que limitaba el uso de los 8 GB de RAM por proceso.
*   **Arranque Live-USB sin desarmar el chasis:** Se aprovechó el parámetro nativo `BOOT_ORDER=0xf21546` de la EEPROM para forzar el arranque desde un pendrive, evitando el complejo proceso de extraer la tarjeta CM4 a una placa portadora (*Carrier Board*).
*   **Flasheo seguro de eMMC:** Se instaló **Raspberry Pi OS 64-bit (Debian 12 - Bookworm)**. Se utilizó la herramienta `rpi-clone` en lugar de `dd` para clonar el sistema de archivos formateando correctamente la eMMC (evitando corrupción por discrepancia de tamaños de disco) y reescribiendo los `PARTUUID` de arranque.
*   **Verificación de Arquitectura:** El sistema ahora corre puramente en 64 bits (`getconf LONG_BIT` = 64), liberando los 8 GB de RAM totales.
*   **Respaldo y Restauración Base:** Se protegieron y restauraron las reglas del udev para el módem 4G LTE (`99-quectel-ttyUSB2-blacklist.rules`) y el script de inicio de usuario (`/etc/rc.local`).

### Resumen

*	**Sistema Operativo:** Raspberry Pi OS 64-bit (Debian 12 Bookworm)  
*	**Dispositivo:** EdgeBox-RPI-200 (Basado en Raspberry Pi Compute Module 4 - CM4)  
*	**Hardware:** 8GB RAM, 32GB eMMC, sin GPU dedicada
*	**credenciales de acceso administrador**
	-	Host: SIP-Edge
	-	Usuario administrador: admin
	-	contraseña: inasc1234

---

---

## 2. Definicion de usuario para aplicacion

Crear el usuario con directorio home y shell bash
```
admin@SIP-Edge:~ $ sudo adduser sipedge
New password:
Retype new password:
passwd: password updated successfully
Changing the user information for sipedge
Enter the new value, or press ENTER for the default
        Full Name []: Analista de Pesaje Materia Extraña
        Room Number []:
        Work Phone []:
        Home Phone []:
        Other []:
chfn: name with non-ASCII characters: 'Analista de Pesaje Materia Extraña'
Is the information correct? [Y/n] Y

```

*	**credenciales de acceso usuario**
- User: sipedge
- password: sipedge1234

ssh sipedge@192.168.1.28

Añadir al usuario a los grupos requeridos
```
admin@SIP-Edge:~ $ sudo usermod -a -G dialout sipedge   # Acceso a puertos serie /dev/ttyACM*
sudo usermod -a -G video sipedge     # Para aceleración gráfica (DRM, framebuffer)
sudo usermod -a -G i2c sipedge       # Si usas algún dispositivo I2C
sudo usermod -a -G gpio sipedge      # Para control de GPIO (si accedes directamente)
sudo usermod -a -G tty sipedge       # Acceso general a terminales
sudo usermod -a -G plugdev sipedge   # Para dispositivos USB (módem 4G)
admin@SIP-Edge:~ $

```

3. Configurar auto-login para el usuario sipedge (modo kiosco)
Queremos que al encender el equipo, inicie sesión automáticamente con el usuario sipedge y lance la interfaz gráfica sin intervención.

Para la interfaz gráfica (LightDM en Raspberry Pi OS)
Edita /etc/lightdm/lightdm.conf:

```bash
sudo nano /etc/lightdm/lightdm.conf
Busca la sección [Seat:*] y descomenta/añade:

ini
[Seat:*]
autologin-user=sipedge
autologin-user-timeout=0
Si el archivo no existe, créalo con ese contenido.
```


## 3. RTC (Reloj de Tiempo Real) - PCF8563

### Estado: ✅ COMPLETADO

### Configuración realizada:
| Componente | Estado | Detalle |
|------------|--------|---------|
| Overlay en config.txt | ✅ | `dtoverlay=i2c-rtc,pcf8563` |
| Detección por kernel | ✅ | Registrado como `rtc0` |
| Comando hwclock | ✅ | Instalado y funcionando |
| Sincronización hora | ✅ | Lectura/escritura correcta |
| Servicio systemd | ✅ | `save-hwclock.service` activo |

### Comandos de verificación:
```bash
sudo hwclock -r          # Lee hora del RTC
sudo hwclock -w          # Guarda hora del sistema en RTC
timedatectl status       # Verifica estado general
```

### Archivos modificados:
- `/boot/firmware/config.txt` - Overlay del RTC
- `/etc/systemd/system/save-hwclock.service` - Servicio de sincronización

### Observaciones:
- El RTC funciona correctamente y mantiene la hora entre reinicios
- El servicio guarda automáticamente la hora al apagar el sistema

## 4.  Módulo 4G LTE - Quectel EC25

### Estado: ✅ COMPLETADO (parcialmente, pendiente plan de datos)

### Configuración realizada:
| Componente | Estado | Detalle |
|------------|--------|---------|
| Detección USB | ✅ | ID `2c7c:0125` |
| Drivers kernel | ✅ | `option`, `qmi_wwan` cargados correctamente|
| Puertos seriales | ✅ | `ttyUSB0`, `ttyUSB1`, `ttyUSB2`, `ttyUSB3` |
| Interfaz de red | ✅ | `wwan0` con IP asignada |
| ModemManager | ✅ | Detecta el módem correctamente |
| ModemManager | ✅ | Envia SMS correctamente |
| SIM card | ✅ | Detectada (Tigo) |
| Señal LTE | ✅ | 89% actual vs. 67%  inicial (con antigua antena wifi) |
| Conexión de datos | ✅ | Bearer activo con IP `10.83.137.6` |
| APN configurado | ✅ | `internet.tigo.com.co` (requiere verificación en punto de despliegue) |
| NetworkManager | ✅ | Conexión "Quectel-4G" creada |

### Configuracion de APNNombre	Tigo Web / Tigo Colombia
*	**APN:**	web.colombiamovil.com.co
*	**Usuario:**	(vacío)
*	**Contraseña:**	(vacío)
*	**Tipo de autenticación:**	PAP
*	**Tipo de APN:**	default, supl


### Comandos de verificación:
*	**comando para ver el estado del modem**: mmcli -m 0
```bash
--------------------------------------------------------------------------------------------------------------------
mmcli -m 0                           # Estado del módem
--------------------------------------------------------------------------------------------------------------------
admin@SIP-Edge:~ $ mmcli -m 0
  ----------------------------------
  General  |                   path: /org/freedesktop/ModemManager1/Modem/0
           |              device id: 84fd4c177c89bd64073a938b9b83c7d2d3c7e76f
  ----------------------------------
  Hardware |           manufacturer: QUALCOMM INCORPORATED
           |                  model: QUECTEL Mobile Broadband Module
           |      firmware revision: EC25AUXGAR08A06M1G
           |         carrier config: default
           |           h/w revision: 10000
           |              supported: gsm-umts, lte
           |                current: gsm-umts, lte
           |           equipment id: 862708046475815
  ----------------------------------
  System   |                 device: /sys/devices/platform/scb/fe9c0000.xhci/usb1/1-1/1-1.3
           |                physdev: /sys/devices/platform/scb/fe9c0000.xhci/usb1/1-1/1-1.3
           |                drivers: option, qmi_wwan
           |                 plugin: quectel
           |           primary port: cdc-wdm0
           |                  ports: cdc-wdm0 (qmi), ttyUSB0 (ignored), ttyUSB1 (gps),
           |                         ttyUSB2 (at), ttyUSB3 (at), wwan0 (net)
  ----------------------------------
  Numbers  |                    own: 573013643187
  ----------------------------------
  Status   |                   lock: sim-pin2
           |         unlock retries: sim-pin (3), sim-puk (10), sim-pin2 (3), sim-puk2 (10)
           |                  state: connected
           |            power state: on
           |            access tech: lte
           |         signal quality: 89% (recent)
  ----------------------------------
  Modes    |              supported: allowed: 2g; preferred: none
           |                         allowed: 3g; preferred: none
           |                         allowed: 4g; preferred: none
           |                         allowed: 2g, 3g; preferred: 3g
           |                         allowed: 2g, 3g; preferred: 2g
           |                         allowed: 2g, 4g; preferred: 4g
           |                         allowed: 2g, 4g; preferred: 2g
           |                         allowed: 3g, 4g; preferred: 4g
           |                         allowed: 3g, 4g; preferred: 3g
           |                         allowed: 2g, 3g, 4g; preferred: 4g
           |                         allowed: 2g, 3g, 4g; preferred: 3g
           |                         allowed: 2g, 3g, 4g; preferred: 2g
           |                current: allowed: 2g, 3g, 4g; preferred: 4g
  ----------------------------------
  Bands    |              supported: egsm, dcs, pcs, g850, utran-1, utran-4, utran-5, utran-8,
           |                         utran-2, eutran-1, eutran-2, eutran-3, eutran-4, eutran-5, eutran-7,
           |                         eutran-8, eutran-28, eutran-40
           |                current: egsm, dcs, pcs, g850, utran-1, utran-4, utran-5, utran-8,
           |                         utran-2, eutran-1, eutran-2, eutran-3, eutran-4, eutran-5, eutran-7,
           |                         eutran-8, eutran-28, eutran-40
  ----------------------------------
  IP       |              supported: ipv4, ipv6, ipv4v6
  ----------------------------------
  3GPP     |                   imei: 862708046475815
           |          enabled locks: fixed-dialing
           |            operator id: 732103
           |          operator name: TIGO
           |           registration: home
           |   packet service state: attached
  ----------------------------------
  3GPP EPS |   ue mode of operation: csps-2
           |    initial bearer path: /org/freedesktop/ModemManager1/Bearer/0
           | initial bearer ip type: ipv4v6
  ----------------------------------
  SIM      |       primary sim path: /org/freedesktop/ModemManager1/SIM/0
           |         sim slot paths: slot 1: /org/freedesktop/ModemManager1/SIM/0 (active)
           |                         slot 2: none
  ----------------------------------
  Bearer   |                  paths: /org/freedesktop/ModemManager1/Bearer/1

```

*	**comando para ver el estado del Bearer**: mmcli -b 1
```bash
---------------------------------------------------------------------------------------------------
mmcli -b 1                           # Estado del bearer
---------------------------------------------------------------------------------------------------
admin@SIP-Edge:~ $ mmcli -b 1
  ------------------------------------
  General            |           path: /org/freedesktop/ModemManager1/Bearer/1
                     |           type: default
  ------------------------------------
  Status             |      connected: yes
                     |      suspended: no
                     |    multiplexed: no
                     |      interface: wwan0
                     |     ip timeout: 20
  ------------------------------------
  Properties         |            apn: internet.tigo.com.co
                     |        roaming: allowed
                     |        ip type: ipv4v6
  ------------------------------------
  IPv4 configuration |         method: static
                     |        address: 10.77.96.236
                     |         prefix: 29
                     |        gateway: 10.77.96.237
                     |            dns: 190.240.115.154, 181.70.124.105
                     |            mtu: 1500
  ------------------------------------
  IPv6 configuration |         method: static
                     |        address: 2803:1800:1351:3f06:a189:3fde:61ba:5826
                     |         prefix: 64
                     |        gateway: 2803:1800:1351:3f06:4192:7c30:3914:2cad
                     |            dns: 2800:e0::ac1d:f00d:5, 2800:e0::ac1d:f00d:6
                     |            mtu: 1500
  ------------------------------------
  Statistics         |     start date: 2026-04-05T22:31:29Z
                     |       duration: 240
                     |       bytes rx: 88
                     |       bytes tx: 96
                     |       attempts: 1
                     | total-duration: 240
                     | total-bytes rx: 88
                     | total-bytes tx: 96
```

*	**comando para ver la ip asignada**: ip addr show wwan0
```bash
---------------------------------------------------------------------------------------------------
ip addr show wwan0                   # IP asignada
---------------------------------------------------------------------------------------------------
admin@SIP-Edge:~ $ ip addr show wwan0
3: wwan0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UNKNOWN group default qlen 1000
    link/none
    inet 10.77.96.236/29 brd 10.77.96.239 scope global noprefixroute wwan0
       valid_lft forever preferred_lft forever
    inet6 2803:1800:1351:3f06:a189:3fde:61ba:5826/64 scope global noprefixroute
       valid_lft forever preferred_lft forever

```

*	**comando para ver la Configuración de red 4G**: nmcli connection show Quectel-4G
```bash
---------------------------------------------------------------------------------------------------
nmcli connection show Quectel-4G     # Configuración de red 4G
---------------------------------------------------------------------------------------------------
admin@SIP-Edge:~ $ nmcli connection show Quectel-4G
connection.id:                          Quectel-4G
connection.uuid:                        b64aa34c-bfde-4787-bb12-020efd653e02
connection.stable-id:                   --
connection.type:                        gsm
connection.interface-name:              --
connection.autoconnect:                 yes
connection.autoconnect-priority:        0
connection.autoconnect-retries:         -1 (default)
connection.multi-connect:               0 (default)
connection.auth-retries:                -1
connection.timestamp:                   1775428289
connection.permissions:                 --
connection.zone:                        --
connection.controller:                  --
connection.master:                      --
connection.slave-type:                  --
connection.port-type:                   --
connection.autoconnect-slaves:          -1 (default)
connection.autoconnect-ports:           -1 (default)
connection.down-on-poweroff:            -1 (default)
connection.secondaries:                 --
connection.gateway-ping-timeout:        0
connection.ip-ping-timeout:             0
connection.ip-ping-addresses:           --
connection.ip-ping-addresses-require-all:-1 (default)
connection.metered:                     unknown
connection.lldp:                        default
connection.mdns:                        -1 (default)
connection.llmnr:                       -1 (default)
connection.dns-over-tls:                -1 (default)
connection.mptcp-flags:                 0x0 (default)
connection.wait-device-timeout:         -1
connection.wait-activation-delay:       -1
ipv4.method:                            auto
ipv4.dns:                               --
ipv4.dns-search:                        --
ipv4.dns-options:                       --
ipv4.dns-priority:                      0
ipv4.addresses:                         --
ipv4.gateway:                           --
ipv4.routes:                            --
ipv4.route-metric:                      -1
ipv4.route-table:                       0 (unspec)
ipv4.routing-rules:                     --
ipv4.replace-local-rule:                -1 (default)
ipv4.dhcp-send-release:                 -1 (default)
ipv4.routed-dns:                        -1 (default)
ipv4.ignore-auto-routes:                no
ipv4.ignore-auto-dns:                   no
ipv4.dhcp-client-id:                    --
ipv4.dhcp-iaid:                         --
ipv4.dhcp-dscp:                         --
ipv4.dhcp-timeout:                      0 (default)
ipv4.dhcp-send-hostname-deprecated:     yes
ipv4.dhcp-send-hostname:                -1 (default)
ipv4.dhcp-hostname:                     --
ipv4.dhcp-fqdn:                         --
ipv4.dhcp-hostname-flags:               0x0 (none)
ipv4.never-default:                     no
ipv4.may-fail:                          yes
ipv4.required-timeout:                  -1 (default)
ipv4.dad-timeout:                       -1 (default)
ipv4.dhcp-vendor-class-identifier:      --
ipv4.dhcp-ipv6-only-preferred:          -1 (default)
ipv4.link-local:                        0 (default)
ipv4.dhcp-reject-servers:               --
ipv4.auto-route-ext-gw:                 -1 (default)
ipv4.shared-dhcp-range:                 --
ipv4.shared-dhcp-lease-time:            0 (default)
ipv6.method:                            auto
---------------------------------------------------------------------------------------------------
```

### Archivos modificados:
- `/etc/NetworkManager/system-connections/Quectel-4G.nmconnection` - Conexión 4G
- `/usr/local/bin/quectel-init.sh` - Script de inicialización (opcional)
- `/etc/systemd/system/quectel-init.service` - Servicio de inicialización

### Scripts para modificar las conexiones de red

-	Muestra el estado actual de conexiones de red (status)
```Bash
sudo /usr/local/bin/switch_network.sh status
```

-	 Habilita la conexion a internet por medio de ethernet
```Bash
sudo /usr/local/bin/switch_network.sh eth
```

-	 Habilita la conexion a internet por medio de 4G (Celular)
```Bash
sudo /usr/local/bin/switch_network.sh 4g
```

-	 Habilita la conexion a internet por medio de manera dual, tanto por ethernet como por 4G.
```
sudo /usr/local/bin/switch_network.sh dual
```

### Scripts para enviar mensajes SMS de prueba
```Bash
sudo /usr/local/bin/send_sms.sh
```

### Observaciones:
- El módem funciona correctamente a nivel de hardware y software
- La conexión a internet requiere plan de datos activo en la SIM
- El envio de mensajes GSM activo y configurado.

### Pendiente:
 Registrar IMEI `862708046475815` en Tigo (15 días) |

---


## 5. Configuración de Puertos Industriales RS232 / RS485
El primer paso es identificar correctamente los puertos. La documentación de SeeedStudio para el EdgeBox-RPI-200 especifica el mapeo de los puertos serie:

RS232: /dev/ttyACM1
RS485: /dev/ttyACM0

Sigue estos pasos para verificar, configurar y probar la comunicación.

Paso 1: Verificar la existencia de los dispositivos

Ejecuta el siguiente comando para listar los dispositivos serie y confirmar que los puertos están presentes:

```Bash
admin@SIP-Edge:~ $ ls -la /dev/ttyACM*
crw-rw---- 1 root dialout 166, 0 Apr  5 17:31 /dev/ttyACM0
crw-rw---- 1 root dialout 166, 1 Apr  5 17:31 /dev/ttyACM1
```

### 2. Configurar permisos de usuario

Para poder comunicarte con los puertos sin ser root, añade tu usuario (por ejemplo, sipedge) al grupo dialout:

```Bash
sudo usermod -a -G dialout sipedge
```

Es necesario cerrar la sesión y volver a iniciarla para que los cambios de grupo surtan efecto.

### 3. Configurar parámetros de comunicación (velocidad, paridad, bits de parada)

Para aplicaciones industriales, la velocidad de 115200 baudios es un estándar. Puedes configurar los parámetros temporalmente con stty o permanentemente en tu script/aplicación.

Configuración temporal con stty (por ejemplo, para RS232):

```Bash
# Configura /dev/ttyACM1 a 115200 baud, 8 bits de datos, sin paridad, 1 bit de parada
stty -F /dev/ttyACM1 115200 cs8 -cstopb -parenb -echo
```
	- 115200: Velocidad en baudios.
	- cs8: 8 bits de datos.
	- cstopb: 1 bit de parada (el '-' significa 'no', por lo que se desactivan 2 bits de parada).
	- parenb: Sin bit de paridad.
	- echo: Desactiva el eco local, útil para comunicación con dispositivos externos.

Configuración en un script de Python:
La configuración se maneja directamente al abrir el puerto. Para RS485, es posible que necesites parámetros adicionales para controlar la dirección de transmisión, pero para empezar, la configuración es similar.

```Bash
#!/usr/bin/env python3
import serial

# Para RS232
ser232 = serial.Serial('/dev/ttyACM1', 115200, timeout=1, bytesize=8, parity='N', stopbits=1)
# Para RS485
ser485 = serial.Serial('/dev/ttyACM0', 115200, timeout=1, bytesize=8, parity='N', stopbits=1)

print(f"RS232 abierto: {ser232.is_open}")
print(f"RS485 abierto: {ser485.is_open}")

# Ejemplo de escritura en RS232
ser232.write(b'1234567890')

# No olvides cerrar los puertos al finalizar
# ser232.close()
# ser485.close()
```
Nota: El manual oficial de EdgeBox-RPI-200 utiliza este ejemplo en Python para verificar la comunicación serie.

### 5.1 Prueba de Comunicación con un Dispositivo Externo

Instalar putty en EdgeBox:+1:

```Bash
sudo apt install putty
```

Conecta un dispositivo externo (o un adaptador USB a RS232/485 en PC) al puerto correspondiente del EdgeBox.
En tu PC, abre un monitor serial (como PuTTY, screen o minicom) en el puerto del adaptador.

En el EdgeBox, usa echo y cat para una prueba rápida:

Enviar datos desde el EdgeBox: En una terminal, ejecuta

```Bash
echo "Hola desde EdgeBox" > /dev/ttyACM1
```
Ahora puedes utilizar putty en el EdgeBox para enviar mensajes a traves del puerto serial hacia el PC y viceversa.


### 6. Inteligencia Artificial (LLMs)
*   **Instalar Ollama:** Ejecutar el script de instalación para el motor de inferencia.
*   **Descarga de Modelos:** Probar modelos cuantizados compatibles con los 8GB de RAM (Recomendados: `Llama 3 8B` o `Phi-3 Mini`).
*   **Monitoreo:** Instalar herramientas como `htop` o `btop` para vigilar la RAM y la temperatura de la CPU durante la generación de texto.


### 7. Periféricos Opcionales (Pendientes por configurar 🛠️)

El sistema base está listo, pero quedan algunos pasos para habilitar todo su potencial y sus periféricos, que no estaban en la configuración original
*   **Hardware Watchdog (WDT):** Configurar un script que envíe pulsos periódicos al GPIO 25 para evitar que el sistema se congele en despliegues remotos.
*	**UPS**: El manual del EdgeBox-RPI-200 indica que la UPS es un **accesorio opcional** que **no está instalada** en este dispositivo.

### Lo que se intentó configurar:
| Componente | Estado | Nota |
|------------|--------|------|
| Overlay gpio-shutdown | ⚠️ Configurado | `dtoverlay=gpio-shutdown,gpio_pin=22,active_low=1,gpio_pull=up` |
| Detección de alarma | ⚠️ Presente | Dispositivo `soc:shutdown_button@16` detectado |
| Apagado automático | ❌ No funciona | El sistema se apaga instantáneamente al perder AC |

### Causa identificada:
El hardware de UPS (supercapacitor CXP-3R0306R y controlador LTC4041) no está presente en el dispositivo, por lo que no hay almacenamiento de energía para mantener el sistema durante el apagado controlado.

### Acción recomendada:
- **Eliminar el overlay** del archivo `config.txt` para evitar comportamientos inesperados O **adquirir el módulo UPS opcional** si se necesita la funcionalidad.

```bash
# Eliminar o comentar la línea en config.txt:
# dtoverlay=gpio-shutdown,gpio_pin=22,active_low=1,gpio_pull=up

# Reiniciar para aplicar cambios
sudo reboot
```

---

## Resumen de Archivos Configurados

| Archivo | Propósito | Estado |
|---------|-----------|--------|
| `/boot/firmware/config.txt` | Overlays RTC, I2C, UART, GPIO | ✅ Configurado |
| `/etc/systemd/system/save-hwclock.service` | Sincronización RTC | ✅ Creado |
| `/etc/NetworkManager/system-connections/Quectel-4G.nmconnection` | Conexión 4G | ✅ Creado |
| `/usr/local/bin/quectel-init.sh` | Inicialización módem | ✅ Creado (opcional) |
| `/etc/systemd/system/quectel-init.service` | Servicio inicialización | ✅ Creado (opcional) |

---

## Servicios Activos

| Servicio | Estado | Función |
|----------|--------|---------|
| `save-hwclock.service` | ✅ Activo | Guarda hora en RTC al apagar |
| `ModemManager` | ✅ Activo | Gestiona el módem 4G |
| `NetworkManager` | ✅ Activo | Gestiona conexiones de red |
| `quectel-init.service` | ✅ Activo | Inicializa módem al inicio |
| `ups-monitor.service` | ❌ No creado | No es necesario (UPS ausente) |

---

## Conclusión

El Hardware del EdgeBox-RPI-200 tiene **todos los periféricos escenciales para su funcionamiento completamente configurados**. La configuración técnica del entorno de software está **completa al 100%**

---