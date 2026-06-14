# Configuración del Hardware Watchdog (WDT) — EdgeBox-RPI-200

> **Ejecutado:** 2026-06-14 — Configuración completada exitosamente.
> Ver Informe 01 §8 para el resumen de la intervención.

---

## 0. Nota sobre el estado pre-existente

Al iniciar la configuración se descubrió que el WDT **ya estaba activo** con un
timeout de 1 minuto, habilitado automáticamente por Raspberry Pi OS mediante el
drop-in `/usr/lib/systemd/system.conf.d/40-rpi-enable-watchdog.conf`:

```ini
# /usr/lib/systemd/system.conf.d/40-rpi-enable-watchdog.conf
[Manager]
RuntimeWatchdogSec=1m
RebootWatchdogSec=2m
```

Esto significó que:
- **El Paso 1 (modprobe) fue innecesario:** el módulo `bcm2835_wdt` es `builtin`
  en el kernel de Raspberry Pi OS y no requiere carga explícita.
- **El Paso 3 (modules-load.d) fue innecesario:** misma razón.
- **El Paso 4 requirió un drop-in adicional:** la configuración en
  `/etc/systemd/system.conf` tiene menor prioridad que los drop-ins. Fue necesario
  crear `/etc/systemd/system.conf.d/50-watchdog-30s.conf` para sobreescribir el
  valor de 1min a 30s.

Las secciones a continuación se mantienen como guía genérica; los pasos marcados
con `[SKIP]` no aplican cuando el módulo es `builtin`.

Habilitar el hardware watchdog del BCM2711 (SoC del Compute Module 4) para cumplir
el requisito `[RNF-003]` del ERS V1.3:

> _Servicios críticos gestionados por systemd con `Restart=always` y watchdog de 30s._

Este procedimiento cierra el pendiente listado en el Informe 01,
sección 7 — _Periféricos Opcionales (Pendientes por configurar)_:

> _Hardware Watchdog (WDT): Configurar un script que envie pulsos periodicos
> al GPIO 25 para evitar que el sistema se congele en despliegues remotos._

**Enfoque usado en este documento:** se utiliza el watchdog interno del SoC
(gestionado por systemd) en lugar de un script manual sobre GPIO 25. Esto es
mas robusto porque systemd alimenta el WDT automaticamente en su main loop; si
el kernel o systemd se cuelgan, el hardware reinicia el sistema sin
intervencion humana.

---

## 2. Hoja de Ruta

```
[Check] → [Backup] → [Paso 1] → [Paso 2] → [Paso 3] → [Paso 4] → [Paso 5] → [Reboot] → [Verify]
```

| Paso | Accion | Depende de |
|------|--------|------------|
| Check | Verificar que el modulo `bcm2835_wdt` existe en el kernel | — |
| Backup | Crear copias timestamped de los 3 archivos a modificar | — |
| Paso 1 | Cargar el modulo y verificar `/dev/watchdog` | Check |
| Paso 2 | Activar watchdog en el device tree (`config.txt`) | Backup |
| Paso 3 | Configurar carga automatica del modulo en boot | Backup |
| Paso 4 | Configurar systemd (`RuntimeWatchdogSec=30`) | Backup |
| Paso 5 | Configurar `sip-edge.service` (`WatchdogSec=30`) | Backup |
| Reboot | Reiniciar el sistema | Pasos 1–5 |
| Verify | Comprobar que el WDT esta activo y operativo | Reboot |

---

## 3. Backup de Archivos Previo a la Intervencion

**Antes de modificar cualquier archivo**, crear copias de seguridad con timestamp
en el mismo directorio del original:

```bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 1. Backup de config.txt
sudo cp /boot/firmware/config.txt /boot/firmware/config.txt.bak.$TIMESTAMP

# 2. Backup de system.conf
sudo cp /etc/systemd/system.conf /etc/systemd/system.conf.bak.$TIMESTAMP

# 3. Backup de sip-edge.service
sudo cp /etc/systemd/system/sip-edge.service /etc/systemd/system/sip-edge.service.bak.$TIMESTAMP

# Verificar los backups creados
ls -la /boot/firmware/config.txt.bak.*
ls -la /etc/systemd/system.conf.bak.*
ls -la /etc/systemd/system/sip-edge.service.bak.*
```

**Anotar el timestamp generado** (ej. `20260614_120000`) para usarlo en la
restauracion si es necesario. Los backups quedan en el mismo directorio que
los originales, lo que permite restaurarlos sin recordar rutas.

> **Nota:** `/etc/modules-load.d/watchdog.conf` es un archivo **nuevo** que
> se creara en el Paso 3. No requiere backup previo — si se necesita volver
> atras, simplemente se elimina.

---

## 4. Configuracion Paso a Paso

### Check — Verificar disponibilidad del modulo

```bash
# Verificar que el modulo existe en el kernel actual
modinfo bcm2835_wdt
```

Salida esperada (ejemplo):
```
filename:       /lib/modules/6.12.75+rpt-rpi-v8/kernel/drivers/watchdog/bcm2835_wdt.ko.xz
license:        GPL
description:    BCM2835 Watchdog Timer driver
author:         Lubomir Rintel
```

**Si `modinfo` falla** (`modinfo: ERROR: Module bcm2835_wdt not found`):
el watchdog no esta compilado en este kernel. **Abortar el procedimiento**
y reportar el bloqueo. No continuar sin el modulo.

---

### Paso 1 — Cargar el modulo y verificar `/dev/watchdog`

```bash
# Cargar el modulo
sudo modprobe bcm2835_wdt

# Verificar que se cargo
lsmod | grep wdt
# bcm2835_wdt            16384  0

# Verificar que el dispositivo existe
ls -la /dev/watchdog*
# crw------- 1 root root 10, 130 Jun 14 12:00 /dev/watchdog
# crw------- 1 root root 252, 0 Jun 14 12:00 /dev/watchdog0
```

Si `/dev/watchdog` y `/dev/watchdog0` no aparecen, el modulo no creo los
dispositivos. Revisar `dmesg | tail -20` para diagnosticar.

---

### Paso 2 — Activar watchdog en el device tree

Agregar la siguiente linea al final de `/boot/firmware/config.txt`:

```
dtparam=watchdog=on
```

```bash
# Verificar que la linea no exista ya
grep -q "dtparam=watchdog" /boot/firmware/config.txt || echo "dtparam=watchdog=on" | sudo tee -a /boot/firmware/config.txt
```

Esta linea instruye al firmware para que habilite el periferico watchdog en el
device tree del BCM2711 al arrancar.

---

### Paso 3 — Carga automatica del modulo en boot

Crear un archivo de configuracion para que el modulo se cargue automaticamente
en cada arranque:

```bash
echo "bcm2835_wdt" | sudo tee /etc/modules-load.d/watchdog.conf
```

Verificar:

```bash
cat /etc/modules-load.d/watchdog.conf
# bcm2835_wdt
```

---

### Paso 4 — Configurar systemd para usar el WDT

Editar `/etc/systemd/system.conf` y cambiar el valor de `RuntimeWatchdogSec`:

```bash
# La linea comentada por defecto:
# #RuntimeWatchdogSec=0

# Cambiar a:
# RuntimeWatchdogSec=30
```

Comando para hacerlo de forma segura:

```bash
sudo sed -i 's/^#RuntimeWatchdogSec=0/RuntimeWatchdogSec=30/' /etc/systemd/system.conf
```

Verificar que el cambio se aplico:

```bash
grep RuntimeWatchdogSec /etc/systemd/system.conf
# RuntimeWatchdogSec=30
```

**Que hace `RuntimeWatchdogSec=30`:**
- systemd abre `/dev/watchdog` al iniciar.
- systemd alimenta el WDT cada 15 segundos (la mitad del timeout).
- Si systemd se cuelga por mas de 30 segundos, el WDT expira y el hardware
  reinicia el sistema.
- Si systemd se detiene limpiamente (`shutdown`/`reboot`), cierra el WDT para
  evitar un reinicio no deseado durante el apagado.

---

### Paso 5 — Configurar sip-edge.service con notificacion WDT

Agregar `WatchdogSec=30` en la seccion `[Service]` del unit de SIP-Edge.

El archivo actual (`/etc/systemd/system/sip-edge.service`):

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

Agregar `WatchdogSec=30` dentro de `[Service]`, quedando asi:

```ini
[Service]
Type=simple
User=sipedge
WorkingDirectory=/home/sipedge/sip_edge
EnvironmentFile=/home/sipedge/sip_edge/.env
ExecStart=/home/sipedge/sip_edge/venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
WatchdogSec=30
```

Comando para aplicar el cambio:

```bash
# Insertar WatchdogSec=30 despues de RestartSec=5
sudo sed -i '/^RestartSec=5/a WatchdogSec=30' /etc/systemd/system/sip-edge.service
```

Verificar:

```bash
grep WatchdogSec /etc/systemd/system/sip-edge.service
# WatchdogSec=30
```

**Que hace `WatchdogSec=30` en el unit:**
- systemd espera que el proceso notifique `WATCHDOG=1` via `sd_notify()`.
- Si el proceso no notifica dentro del timeout, systemd lo mata y aplica
  `Restart=always`.
- Si el proceso esta en vivo y notifica correctamente, no hay accion.
- **Importante:** uvicorn no implementa `sd_notify()` nativamente. Esto se
  habilita mediante la dependencia `sdnotify` de Python o con un wrapper.

> **Nota sobre uvicorn y WDT:**
> Actualmente uvicorn no emite notificaciones WATCHDOG a systemd. Si se desea
> que systemd _reinicie_ uvicorn cuando se cuelga (en lugar de reiniciar todo
> el sistema), se requiere un cambio adicional en el codigo de la aplicacion
> (agregar `sd_notify` o usar `Type=notify`). Sin este cambio, el unico WDT
> activo es el de systemd a nivel sistema (Paso 4), que **SI** reinicia el
> equipo completo si systemd se congela. Para el alcance inmediato
> (`[RNF-003]`), esto es suficiente.

---

## 5. Verificacion

### 5.1 Post-reboot — Verificar dispositivo y modulo

```bash
# Verificar que el modulo esta cargado
lsmod | grep wdt
# bcm2835_wdt            16384  0

# Verificar dispositivos watchdog
ls -la /dev/watchdog*
# crw------- 1 root root  10, 130 Jun 14 12:05 /dev/watchdog
# crw------- 1 root root 252,   0 Jun 14 12:05 /dev/watchdog0
```

### 5.2 Verificar mensajes del kernel

```bash
dmesg | grep -i watchdog
```

Salida esperada (ejemplo):
```
[    2.345678] bcm2835_wdt bcm2835_wdt: Broadcom BCM2835 watchdog timer
```

### 5.3 Verificar configuracion de systemd

```bash
systemctl show -p RuntimeWatchdogSec
# RuntimeWatchdogSec=30

systemctl show -p WatchdogTimestamp
# WatchdogTimestamp=Sat 2026-06-14 12:05:00 UTC
```

Si `WatchdogTimestamp` muestra una fecha/hora, systemd abrio `/dev/watchdog`
correctamente y esta alimentandolo.

### 5.4 Verificar estado del servicio sip-edge

```bash
systemctl show sip-edge.service -p WatchdogSec
# WatchdogSec=30
```

### 5.5 Prueba funcional — Timeout forzado (solo en entorno controlado)

> **Advertencia:** esta prueba fuerza un kernel panic y el sistema se reiniciara.
> Realizarla **solo** si se tiene acceso fisico al dispositivo o SSH con
> reconexion automatica. No ejecutar en produccion con pesajes activos.

```bash
# Forzar un kernel panic — el WDT debe reiniciar el sistema en ~30 segundos
echo c | sudo tee /proc/sysrq-trigger
```

Tras ~30 segundos, el EdgeBox debe reiniciarse automaticamente. Verificar
que el sistema vuelve a estar operativo tras el reinicio:

```bash
uptime
# up 1 minute  (o similar, indicando que se reinicio)
```

---

## 6. Rollback y Restauracion

Se documentan dos opciones mutuamente excluyentes. La Opcion A es el
procedimiento principal; la Opcion B es la alternativa de restauracion
completa si la Opcion A falla (cosa que no deberia ocurrir).

Ambas opciones asumen que se tiene acceso SSH al dispositivo y que el
timestamp de los backups es conocido (ver seccion 3).

---

### Opcion A — Rollback suave (deshabilitar WDT sin restaurar backups)

Esta opcion desactiva el watchdog a nivel de systemd manteniendo el modulo y
el device tree intactos. `/dev/watchdog` seguira existiendo pero ni systemd
ni ningun servicio lo abriran, por lo que no hay riesgo de reinicio espontaneo.

**Ventaja:** solo modifica una linea, rapido de aplicar (~10 segundos).
**Desventaja:** deja configuracion residual (modulo cargado, device tree
habilitado). Inofensivo, pero no es un regreso al estado exacto pre-intervencion.

```bash
# 1. Deshabilitar RuntimeWatchdogSec en system.conf
sudo sed -i 's/^RuntimeWatchdogSec=30/#RuntimeWatchdogSec=0/' /etc/systemd/system.conf

# 2. Recargar configuracion de systemd
sudo systemctl daemon-reload

# 3. Reiniciar para que systemd suelte /dev/watchdog
sudo reboot
```

Tras el reinicio, verificar que el WDT no esta activo:

```bash
systemctl show -p RuntimeWatchdogSec
# RuntimeWatchdogSec=0

systemctl show -p WatchdogTimestamp
# WatchdogTimestamp=
```

`WatchdogTimestamp=` vacio confirma que systemd **no** abrio `/dev/watchdog`.

---

### Opcion B — Restauracion completa desde backups

Esta opcion revierte **todos** los archivos a su estado exacto pre-intervencion,
incluyendo comentarios, formato y whitespace original.

**Requisito:** conocer el timestamp de los backups (ej. `20260614_120000`).
Reemplazar `<TIMESTAMP>` por el valor real anotado en la seccion 3.

```bash
TIMESTAMP="<TIMESTAMP>"   # Reemplazar con el valor real, ej. 20260614_120000

# 1. Restaurar config.txt original
sudo cp /boot/firmware/config.txt.bak.$TIMESTAMP /boot/firmware/config.txt

# 2. Restaurar system.conf original
sudo cp /etc/systemd/system.conf.bak.$TIMESTAMP /etc/systemd/system.conf

# 3. Restaurar sip-edge.service original
sudo cp /etc/systemd/system/sip-edge.service.bak.$TIMESTAMP /etc/systemd/system/sip-edge.service

# 4. Eliminar archivo nuevo creado en Paso 3
sudo rm -f /etc/modules-load.d/watchdog.conf

# 5. Recargar configuracion de systemd
sudo systemctl daemon-reload

# 6. Reiniciar
sudo reboot
```

Tras el reinicio, verificar que no hay rastro del WDT:

```bash
# El modulo no debe estar cargado
lsmod | grep wdt
# (sin salida)

# Los dispositivos no deben existir (o no deben ser accesibles)
ls -la /dev/watchdog*
# ls: cannot access '/dev/watchdog*': No such file or directory

# systemd no debe reportar watchdog
systemctl show -p RuntimeWatchdogSec
# RuntimeWatchdogSec=0

systemctl show -p WatchdogTimestamp
# WatchdogTimestamp=
```

### Verificar integridad de los archivos restaurados

```bash
# Deben ser identicos al original (diff sin salida = identicos)
diff /boot/firmware/config.txt.bak.$TIMESTAMP /boot/firmware/config.txt || echo "OK: identicos"
diff /etc/systemd/system.conf.bak.$TIMESTAMP /etc/systemd/system.conf || echo "OK: identicos"
diff /etc/systemd/system/sip-edge.service.bak.$TIMESTAMP /etc/systemd/system/sip-edge.service || echo "OK: identicos"
```

Si algun `diff` muestra diferencias, la restauracion no fue exitosa. Ejecutar
el bloque de copias de nuevo verificando el timestamp.

---

## 7. Referencias

| Fuente | Detalle |
|--------|---------|
| **Informe 01 §7** | Watchdog listado como periferico pendiente de configurar |
| **ERS V1.3 `[RNF-003]`** | Recuperacion ante fallos: systemd + watchdog de 30s |
| **BCM2711 Peripherals Spec** | Watchdog Timer en el SoC del CM4 |
| **systemd.system.conf(5)** | Documentacion de `RuntimeWatchdogSec=` |
| **systemd.service(5)** | Documentacion de `WatchdogSec=` |
| **kernel docs** | `Documentation/watchdog/watchdog-api.rst` |
