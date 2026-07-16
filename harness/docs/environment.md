# Environment â€” sip_edge

> El agente DEBE leer este archivo **antes de ejecutar cualquier comando bash**.
> Describe DONDE y COMO se ejecutan los comandos, y que servicios estan disponibles.

---

## 1. Modos de ejecucion

Este proyecto tiene **dos entornos** distintos:

| Entorno | Proposito | Como acceder |
|---------|-----------|-------------|
| **Local (dev)** | Desarrollo, tests, specs | Docker compose en la maquina local |
| **EdgeBoxes (prod)** | 2 EdgeBox-RPI-200 (ver §2 inventario) | SSH a 192.168.1.42 (solo uno en linea a la vez) |

---

## 2. EdgeBoxes (Producción)

El proyecto tiene **dos EdgeBox-RPI-200** con hardware idéntico. Solo uno está conectado
a la red a la vez (misma IP `192.168.1.42`).

### Inventario

| ID | CPU Serial | MAC eth0 | Machine ID | IMEI Modem | Estado |
|----|-----------|----------|------------|------------|--------|
| **EB1** | `10000000b9e9541c` | `2c:cf:67:bb:3a:de` | `6b8419ea3...` | `862708046456880` | PROD — WiFi pendiente |
| **EB2** | *(pendiente)* | *(pendiente)* | *(pendiente)* | `862708046475815` | TEST — fallo SMS (F28) |

> ⚠️ **Identificador primario: CPU Serial** (`grep Serial /proc/cpuinfo`).
> El IMEI puede variar si se intercambia el módem Quectel entre dispositivos.

### Hardware (común a ambos)

| Componente | Detalle |
|------------|---------|
| **Dispositivo** | EdgeBox-RPI-200 (SeeedStudio) |
| **CPU** | Raspberry Pi CM4 â€” 4x Cortex-A72 @ 1.5 GHz (aarch64) |
| **RAM** | 8 GB |
| **Almacenamiento** | 32 GB eMMC |
| **SO** | Debian 13 (Trixie) aarch64, kernel 6.12 |
| **Hostname** | SIP-Edge |

### Acceso SSH

```bash
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42
```

| Parametro | Valor |
|-----------|-------|
| **Clave privada** | `~/.ssh/sip_edge_edgebox` (dedicada, generada en setup) |
| **Usuario** | `sipedge` |
| **IP Ethernet** | `192.168.1.42/24` |
| **Password sudo** | `sipedge1234` (usar `sudo -S` para comandos batch; sudo requiere tty) |

### Red

| Interfaz | Tipo | IP | Estado |
|----------|------|----|--------|
| `eth0` | Ethernet | 192.168.1.42/24 | UP |
| `wwan0` | 4G LTE (Quectel EC25) | DHCP del operador | Configurado (plan de datos pendiente) |

### Modem 4G â€” Quectel EC25

| Parametro | Valor |
|-----------|-------|
| **IMEI** | Por EdgeBox (ver §2 inventario) |
| **Operador** | Tigo Colombia (732103) |
| **APN** | `internet.tigo.com.co` |
| **Numero** | Por EdgeBox (ver §2 inventario) |
| **Puertos AT** | `/dev/ttyUSB2`, `/dev/ttyUSB3` |
| **Gestion** | ModemManager (`mmcli -m 0`) |

### Puertos seriales industriales

| Puerto fisico | Dispositivo | Proposito |
|--------------|-------------|-----------|
| RS485 | `/dev/ttyACM0` | Bascula DINI ARGEO DFWLI-2 |
| RS232 | `/dev/ttyACM1` | Transmision a PC externo |

- Permisos: `root:dialout` â€” el usuario `sipedge` esta en el grupo `dialout`.
- Parametros por defecto: 115200 baud, 8 data bits, sin paridad, 1 stop bit.

### RTC (Real-Time Clock)

| Componente | Detalle |
|------------|---------|
| **Chip** | PCF8563 (I2C) |
| **Dispositivo** | `/dev/rtc0` |
| **Sincronizacion** | `save-hwclock.service` activo |

### Watchdog (WDT)

| Parametro | Valor |
|-----------|-------|
| **Hardware** | BCM2711 (`bcm2835_wdt`) |
| **Timeout** | 30 segundos (`RuntimeWatchdogSec=30`) |
| **Dispositivo** | `/dev/watchdog`, `/dev/watchdog0` |

---

## 3. Software en la EdgeBox

### Servicios systemd (todos `enabled`)

| Servicio | Puerto | Funcion |
|----------|--------|---------|
| `mariadb.service` | 3306 (localhost) | Base de datos |
| `sip-edge.service` | 8000 (0.0.0.0) | Backend FastAPI |
| `ModemManager.service` | â€” | Gestion modem 4G |
| `NetworkManager.service` | â€” | Gestion de red |
| `ssh.service` | 22 | Acceso remoto |
| `cron.service` | â€” | Tareas programadas |

### Base de datos â€” MariaDB

| Parametro | Valor |
|-----------|-------|
| **Version** | 11.8.6 |
| **Engine** | InnoDB |
| **Base de datos** | `sip_edge` |
| **Usuario** | `sip_user`@`localhost` |
| **Password** | `sip_pass` |
| **Socket** | `/run/mysqld/mysqld.sock` |

### Aplicacion SIP-Edge

| Parametro | Valor |
|-----------|-------|
| **Ubicacion** | `/home/sipedge/sip_edge/` |
| **Python** | 3.13.5 en venv (`/home/sipedge/sip_edge/venv/`) |
| **Config YAML** | `/home/sipedge/sip_edge/config.yaml` |
| **Variables entorno** | `/home/sipedge/sip_edge/.env` |
| **DEV_MODE** | `false` (hardware real activo) |
| **API** | `http://192.168.1.42:8000` |

### llama.cpp â€” Motor de inferencia LLM

| Parametro | Valor |
|-----------|-------|
| **Version** | b9632 (ggml v0.15.1) |
| **Binarios** | 49 herramientas en `/usr/local/bin/` |
| **Servidor** | `llama-server` en puerto 8080 |
| **Modelos** | `/home/models/*.gguf` (~4.9 GB total) |

Modelos disponibles:
| Modelo | Tamano | Cuantizacion |
|--------|--------|-------------|
| `qwen2.5-1.5b-instruct-q4_k_m.gguf` | 1.1 GB | Q4_K_M |
| `gemma-4-E2B-it-Q4_K_M.gguf` | 2.9 GB | Q4_K_M |
| `Qwen3.5-2B-UD-Q2_K_XL.gguf` | 922 MB | Q2_K_XL |

---

## 4. Entorno Local (Desarrollo)

### Docker Compose

```bash
# Iniciar servicios
docker compose up -d

# Verificar
docker compose ps

# Detener
docker compose down
```

### Servicios en Docker

| Servicio | Container | Puerto host |
|----------|----------|-------------|
| Backend (FastAPI) | `sip_edge_backend` | 8000 |
| MariaDB | `sip_edge_db` | 3306 |

### Variables de entorno (dev)

Definidas en `compose.yml` (no en `.env`). Valores por defecto:
```
DB_HOST=mariadb
DB_NAME=sip_edge
DB_USER=sip_user
DB_PASSWORD=sip_pass
JWT_SECRET_KEY=sip_edge_jwt_secret_key_dev
ADMIN_DEFAULT_PASSWORD=admin
DEV_MODE=true
```

### Shell

**Todos los comandos que interactuan con el codigo deben ejecutarse dentro del contenedor:**

```bash
# Tests
docker compose exec backend python -m unittest discover -s tests -v

# Instalar dependencias
docker compose exec backend pip install -r requirements.txt

# Ver init
./init.ps1
```

### Volumenes montados (live-reload en dev)

- `./src` â†’ `/app/src`
- `./tests` â†’ `/app/tests`
- `./harness` â†’ `/app/harness`


### Frontend (SPA Svelte 5)

El frontend es un SPA construido con Svelte 5.

- **Fuente:** `frontend/src/`
- **Servido desde:** `src/static/` (backen lo sirve en `/static/`)
- **Ciclo de desarrollo:**

  ```bash
  # 1. Modificar componentes en frontend/src/components/
  # 2. Compilar:
  Set-Location -LiteralPath "frontend"
  npm run build
  # 3. Copiar a src/static/ (donde el backend lo sirve):
  Remove-Item -LiteralPath "src/static" -Recurse -Force
  Copy-Item -Recurse -Path "frontend/dist/*" -Destination "src/static/"
  ```

  El volumen `./src:/app/src` en Docker hace que los cambios en `src/static/`
  se reflejen instantaneamente en el contenedor — **no require reiniciar el backend**.

- **IMPORTANTE:** `src/static/` contiene el bundle compilado del frontend.
  Si solo modificas archivos en `frontend/src/` sin rebuild + copy, los cambios
  **NO** se veran reflejados en el navegador. Este es un error comun.
  Verifica siempre que `src/static/index.html` tenga fecha/hora de build reciente.

- **Tests de frontend:**
  ```bash
  Set-Location -LiteralPath "frontend"
  npm test
  ```


## ReCamera 2002w 64GB (Seeed Studio)

Cámara AI edge conectada al EdgeBox. Usada para captura cenital de imágenes
de muestras de materia extraña (Feature 32: sample_imaging).

| Parámetro | Valor |
|-----------|-------|
| **IP Ethernet** | 192.168.1.44 (DHCP del router) |
| **IP USB (RNDIS)** | 192.168.42.1 (cuando conectada por USB-C) |
| **AP WiFi** | SSID reCamera_XXXXXX, IP 192.168.16.1, pass 12345678 |
| **MAC Ethernet** | 2c:f7:f1:21:3c:b2 |
| **MAC WiFi** | 60:ff:9e:02:f5:9b (AzureWave) |
| **WebUI** | http://192.168.1.44/ o http://192.168.42.1/ |
| **Password WebUI** | sipedge1234* |
| **Firmware** | 0.2.4 (actualizado desde 0.2.1 vía OTA) |
| **Puertos** | 22 (SSH), 80 (WebUI), 554 (RTSP), 1880 (Node-RED), 9090 (terminal) |

### Acceso desde EdgeBox
`ash
# Vía Ethernet
curl http://192.168.1.44/
curl http://192.168.1.44/api/version

# Vía USB (requiere firmware >= 0.2.2)
curl http://192.168.42.1/
`

### Notas
- Firmware < 0.2.2 tiene bug CDC ACM vs NCM en Linux (NETDEV WATCHDOG timeout en usb0).
- Para actualizar: WebUI → Sidebar → System → Software Update → Check → Apply.
- Modo AP WiFi solo disponible si no está conectada por Ethernet o USB.

---

## 5. Comandos utiles

### En la EdgeBox (via SSH)

```bash
# Estado del servicio
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "sudo systemctl status sip-edge"

# Logs en tiempo real
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "sudo journalctl -u sip-edge -f"

# Reiniciar servicio
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "sudo systemctl restart sip-edge"

# Actualizar codigo (git pull + restart)
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "cd /home/sipedge/sip_edge && git pull && sudo systemctl restart sip-edge"

# Estado del modem 4G
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "mmcli -m 0"

# Verificar puertos seriales
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "ls -la /dev/ttyACM*"

# Verificar MariaDB
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "sudo systemctl status mariadb"


### Acceso a MariaDB en la EdgeBox

```bash
# Opcion A — Query directa via SSH (siempre funciona)
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 \
  "mysql -usip_user -psip_pass sip_edge -e 'SELECT COUNT(*) FROM users;'"

# Opcion B — Tunel SSH + cliente grafico local (recomendado)
# En tu PC local, abre un tunel:
ssh -i ~/.ssh/sip_edge_edgebox -L 3307:localhost:3306 sipedge@192.168.1.42
# Deja esta terminal abierta. Conectate desde HeidiSQL/DBeaver/MySQL Workbench a:
#   Host: 127.0.0.1  Port: 3307  User: sip_user  Pass: sip_pass  DB: sip_edge

# Opcion C — phpMyAdmin liviano sin Apache (YA INSTALADO)
# Ya instalado en ~/phpMyAdmin-5.2.2-all-languages
# Iniciar:
#    ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "php -S 0.0.0.0:8080 -t ~/phpMyAdmin-5.2.2-all-languages &"
# Abrir: http://192.168.1.42:8080 (user: sip_user, pass: sip_pass)
# Detener:
#    ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "pkill -f 'php -S'"

```
# Ejecutar tests de hardware en EdgeBox (post-deploy)
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "cd /home/sipedge/sip_edge && source venv/bin/activate && python -m unittest discover -s tests_hardware -v"

# Smoke test de health check en EdgeBox
curl http://192.168.1.42:8000/health

# Logs del servicio tras deploy
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "sudo journalctl -u sip-edge --no-pager -n 50"```

### En local (desarrollo Docker)

```bash
# API health check
curl http://127.0.0.1:8000/health

# Ejecutar un test especifico
docker compose exec backend python -m unittest tests.test_config.TestConfigEndpoints.test_get_config_returns_200 -v

# Ver dependencias instaladas
docker compose exec backend pip list
```

