# Informe de Configuración — reCamera 2002w 64GB

> **Fecha:** 2026-07-14 / 2026-07-15
> **Dispositivo:** Seeed Studio reCamera 2002w 64GB
> **Firmware:** 0.2.4 (actualizado desde 0.2.1 vía OTA)
> **Objetivo:** Configurar cámara AI edge para captura cenital de muestras
> (Feature 32: sample_imaging) y establecer conectividad WiFi AdHoc con EdgeBox

---

## 1. Hardware

| Componente | Detalle |
|---|---|
| **Dispositivo** | reCamera 2002w 64GB (Seeed Studio) |
| **SKU** | 102991897 |
| **Chip** | Sophgo SG2002 — RISC-V + ARM, 1 TOPS @INT8 |
| **Cámara** | OV5647, 5 MP |
| **Almacenamiento** | 64 GB eMMC |
| **WiFi** | 802.11 b/g/n, chip AzureWave (`60:ff:9e:02:f5:9b`) |
| **Ethernet** | 10/100 Mbps, MAC `2c:f7:f1:21:3c:b2` |
| **Alimentación** | USB-C (5V). NO es PoE — el Ethernet es solo datos |
| **LED iluminación** | Luz blanca controlable vía MQTT |
| **SO** | Buildroot Linux, kernel 5.10.4 RISC-V |

---

## 2. Conectividad

### 2.1 Métodos de conexión

| Método | IP cámara | Medio físico | Notas |
|---|---|---|---|
| USB-C (RNDIS) | `192.168.42.1` | Cable USB al host | Crea interfaz `usb0` vía CDC NCM. Requiere firmware ≥0.2.2 |
| Ethernet | DHCP del router | Cable Ethernet | No requiere configuración adicional |
| WiFi AP mode | `192.168.16.1` | SSID `reCamera_02F9D5` | Password `12345678`. Solo activo sin Ethernet ni USB |

### 2.2 Configuración WiFi AdHoc con EdgeBox

La cámara se conecta al EdgeBox vía WiFi en modo AP. El EdgeBox es cliente WiFi.

| Parámetro | Valor |
|---|---|
| SSID | `reCamera_02F9D5` |
| Password WiFi | `12345678` |
| IP cámara | `192.168.16.1/24` |
| IP EdgeBox (wlan0) | `192.168.16.226/24` (DHCP de la cámara) |
| Comando de conexión | `nmcli dev wifi connect "reCamera_02F9D5" password "12345678"` |

**Nota:** La ruta `eth0` (métrica 100) tiene prioridad sobre `wlan0` (métrica 600).
El SSH al EdgeBox (`192.168.1.42`) no se ve afectado.

---

## 3. Software y Servicios

### 3.1 Servicios activos

| Servicio | Puerto | Descripción |
|---|---|---|
| **WebUI** | 80 | SPA React para gestión (config, network, system, files) |
| **Node-RED** | 1880 | Backend programable. Flows visuales para cámara e IA |
| **SSCMA Supervisor** | 8090 (interno) | Orquestador del pipeline de cámara e inferencia |
| **SSCMA Node** | — | Puente MQTT entre Node-RED y Supervisor |
| **MQTT Broker** | 1883 (localhost) | Comunicación interna SSCMA ↔ Node-RED |
| **SSH** | 22 | Acceso remoto |
| **Terminal Web** | 9090 | ttyd — terminal vía navegador |

### 3.2 Acceso SSH

| Parámetro | Valor |
|---|---|
| Usuario | `recamera` (NO `root`) |
| Password | `sipedge1234*` (misma que WebUI) |
| Password sudo | igual que arriba |
| Uso con sudo | `echo "sipedge1234*" \| sudo -S comando` |

### 3.3 Inicio de servicios en boot

| Orden | Script | Servicio |
|---|---|---|
| S03 | `S03node-red` | Node-RED (`/usr/bin/node-red-pi --max-old-space-size=64 --expose-gc`) |
| S91 | `S91sscma-node` | SSCMA Node (puente MQTT) |
| S93 | `S93sscma-supervisor` | Supervisor del pipeline de cámara |
| S95 | `S95frame-capture` | Captura de frames vía MQTT (personalizado) |
| S98 | `S98ttyd` | Terminal web |
| S99 | `S99user` | Configuración de usuario |

**Importante:** El orden `S91` → `S93` → `S03` es crítico. Si Node-RED
arranca antes que SSCMA Node, los nodos camera/model no se inicializan.

### 3.4 Node-RED

| Parámetro | Valor |
|---|---|
| Versión | 4.1.0 |
| Node.js | 22.8.0 |
| Binario | `/usr/bin/node-red-pi` (NO `red.js`) |
| Flags | `--max-old-space-size=64 --expose-gc` |
| httpNodeRoot | `/` (endpoints HTTP en raíz) |
| Flows | `/home/recamera/.node-red/flows.json` |
| Flow backup | `/home/recamera/.node-red/.flows.json.backup` |
| Auth editor | Sin autenticación (POST /flows acepta sin credenciales) |

**Paletas instaladas:**
- `node-red-contrib-sscma` — nodos Vision AI: camera, model, capture, stream, save, preview
- `node-red-dashboard` — FlowFuse Dashboard (UI para preview)
- `node-red-contrib-os` — nodos de sistema

### 3.5 Pipeline de cámara e IA

```
┌──────────────────────────────────────────────────┐
│ OV5647 Sensor                                     │
│   ↓                                               │
│ SSCMA Supervisor (CV181x ISP + NPU)               │
│   ↓ MQTT (localhost:1883)                         │
│ ┌──────────────────────────────────────────────┐ │
│ │ Node-RED                                     │ │
│ │  [camera] → [model: YOLO11n] → [preview]     │ │
│ │                ↓ MQTT out                     │ │
│ │      topic: sscma/v0/recamera/node/out/<id>  │ │
│ │      {data: {image: "<base64 JPEG>"}}         │ │
│ └──────────────────────────────────────────────┘ │
│   ↓ frame-save.py (decode base64 → JPEG)         │
│ /tmp/last_frame.jpg                               │
└──────────────────────────────────────────────────┘
```

**Modelo cargado:** YOLO11n Detection (Ultralytics), compilado para NPU CV181x
**Ruta:** `/usr/share/supervisor/models/yolo11n_detection_cv181x_int8.cvimodel`
**Resolución:** 1920×1080 @ 30fps captura, 640×640 inferencia
**Tiempo de carga:** ~60 segundos tras boot o deploy

---

## 4. Captura de Imágenes vía HTTP

### 4.1 Endpoint

| Parámetro | Valor |
|---|---|
| URL | `GET http://192.168.16.1:1880/foto` |
| Response | `image/jpeg`, 640×640, ~17 KB |
| Flow Node-RED | `http in` → `file in` → `http response` |
| Archivo fuente | `/tmp/last_frame.jpg` |

### 4.2 Servicio de captura (`S95frame-capture`)

| Parámetro | Valor |
|---|---|
| Script | `/etc/init.d/S95frame-capture` |
| Python helper | `/usr/local/bin/frame-save.py` |
| Método | `mosquitto_sub` escucha MQTT, decodifica base64, guarda JPEG |
| Control | `sudo /etc/init.d/S95frame-capture {start\|stop\|status}` |

**⚠️ El servicio de captura interfiere con el preview.** Si se observa
"connection lost" o lag en el dashboard, detener la captura:
```bash
echo sipedge1234* | sudo -S /etc/init.d/S95frame-capture stop
```

### 4.3 Flow exportado

El flow de Node-RED para el endpoint `/foto` está exportado en:
`/home/sipedge/foto.flow.json` (en el EdgeBox).

Para importarlo en un dashboard restaurado:
1. Abrir `http://192.168.16.1:1880`
2. Menú → Import → seleccionar archivo o pegar JSON
3. Deploy

---

## 5. Control de Luz LED

La luz blanca de iluminación se controla vía MQTT:

```bash
# Encender
echo '{"code":0,"data":["light",1],"name":"light","type":0}' | \
  mosquitto_pub -h localhost -t sscma/v0/recamera/node/in/89ecdff83571f71a -s

# Apagar (cambiar 1 por 0)
```

---

## 6. Troubleshooting

### 6.1 Preview no muestra imagen
**Síntoma:** Dashboard preview carga pero no hay video.
**Causas probables:**
1. `sscma-node` no está corriendo → `ps | grep sscma-node`
2. Modelo YOLO destruido (timeout de carga) → revisar MQTT: `mosquitto_sub -t 'sscma/v0/recamera/#' -v`
3. Servicio de captura consumiendo recursos → detener con `S95frame-capture stop`
**Fix:** Reiniciar cámara. El orden natural de boot (S91→S93→S03) es el más fiable.

### 6.2 "Connection lost" intermitente en preview
**Causa:** El servicio `S95frame-capture` compite por MQTT con el pipeline camera→model→preview.
**Fix:** Detener el servicio de captura.
**Root cause:** El shell loop `while true; do mosquitto_sub -C 1 | python3; done`
genera sobrecarga de reconexión MQTT que afecta al WebSocket del dashboard.

### 6.3 /foto devuelve 0 bytes
**Causa:** Modelo YOLO no cargado o destruido. Sin modelo no hay frames MQTT.
**Fix:** Esperar 60s tras boot. Si persiste, verificar `sscma-node` y redeployar.

### 6.4 Node-RED no responde tras modificar flows por API
**Causa:** El flow de 90 nodos + 64MB RAM satura Node-RED.
**Fix:** Usar siempre `sudo /etc/init.d/S03node-red restart`. Nunca `node red.js` directo.

### 6.5 USB-C no funciona en Linux (NETDEV WATCHDOG timeout)
**Causa:** Firmware ≤0.2.1 tiene bug CDC ACM vs NCM.
**Fix:** Actualizar a ≥0.2.2 vía WebUI → System → Software Update.

---

## 7. Lecciones Aprendidas

| # | Lección |
|---|---|
| 1 | El orden de boot es crítico: sscma-node (S91) antes que Node-RED (S03) |
| 2 | YOLO necesita ~60s para cargar. No interrumpir con redeploys |
| 3 | El nodo `camera` de Node-RED no emite frames — solo el `model` vía MQTT |
| 4 | MQTT solo en localhost (127.0.0.1). No accesible desde el EdgeBox |
| 5 | Servicio de captura y preview no coexisten bien. Usar bajo demanda |
| 6 | Cerrar el editor Node-RED antes de desplegar por API (evita double-destroy) |
| 7 | SSH user es `recamera` (NO `root`), password = WebUI password |
| 8 | `sudo` en la cámara requiere `-S` con password por stdin |
| 9 | Para comandos multinivel (PS→SSH→SSH), usar base64 para evitar escaping |
| 10 | Con firmware 0.2.4, el AP mode WiFi funciona solo sin Ethernet ni USB conectados |

---

## 8. Referencias

| Recurso | URL |
|---|---|
| Wiki oficial | https://wiki.seeedstudio.com/recamera_getting_started/ |
| OS repo | https://github.com/Seeed-Studio/reCamera-OS |
| SSCMA examples | https://github.com/Seeed-Studio/sscma-example-sg200x |
| Hardware OSHW | https://github.com/Seeed-Studio/OSHW-reCamera-Series |
| Learnings (local) | `harness/learnings/recamera.md` |
| Environment (local) | `harness/docs/environment.md` — sección ReCamera |