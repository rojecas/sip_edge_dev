# Aprendizajes — reCamera 2002w (Seeed Studio)

> Sesión 2026-07-14 — Conexión WiFi, captura de imagen vía MQTT + Node-RED

## Hardware y conectividad

### Métodos de conexión
| Método | IP cámara | Medio | Notas |
|--------|-----------|-------|-------|
| USB-C (RNDIS) | 192.168.42.1 | Cable USB al host | Requiere firmware >= 0.2.2 para Linux |
| Ethernet | DHCP del router | Cable Ethernet | NO es PoE — necesita USB-C para alimentación |
| WiFi AP mode | 192.168.16.1 | SSID `reCamera_XXXXXX` | Password `12345678`. Solo se activa sin Ethernet ni USB conectados |

### Firmware
- **v0.2.1**: Bug CDC ACM vs NCM en Linux → `NETDEV WATCHDOG timeout` en `usb0`
- **v0.2.2+**: Corregido. Deshabilita CDC ACM para que CDC NCM funcione en Linux
- **v0.2.4**: Última versión. Agrega WiFi Halow y detección de voltaje de batería
- **Actualización OTA**: WebUI → Sidebar → System → Software Update → Check → Apply

### SSH
- **Usuario**: `recamera` (NO `root`)
- **Password**: la misma que la WebUI (default: `recamera`)
- **sudo password**: misma que WebUI
- SSH se habilita por defecto desde v0.2.2. Usar `-S` para sudo en scripts: `echo password | sudo -S comando`

### WiFi AdHoc con EdgeBox
- EdgeBox se conecta como cliente WiFi al AP de la cámara
- Comando: `nmcli dev wifi connect "reCamera_XXXXXX" password "12345678"`
- La cámara asigna IP al EdgeBox por DHCP en 192.168.16.0/24
- La ruta por eth0 (métrica 100) tiene prioridad sobre wlan0 (métrica 600) — no afecta SSH

## Captura de imágenes

### ❌ Lo que NO funciona
1. **No hay endpoint REST de snapshot**: `/api/snapshot`, `/snapshot.jpg`, etc. redirigen al SPA
2. **No hay V4L2 estándar**: la cámara usa ISP de Sophgo CV181x (`/dev/cvi-vi`, no `/dev/video0`)
3. **RTSP solo si se configura en Node-RED**: requiere nodo `stream` en un flow activo
4. **Nodo `camera` de Node-RED no emite frames por sus wires**: solo mensajes de control `{code, data, name, type}`
5. **MQTT solo en localhost**: broker en 127.0.0.1:1883, no accesible desde fuera de la cámara

### ✅ Lo que SÍ funciona
1. **El modelo YOLO publica frames en MQTT**: topic `sscma/v0/recamera/node/out/<model_node_id>`
2. **El frame viene en base64** dentro de `msg.data.image` (JPEG, 640×640)
3. **`mosquitto_sub` desde la cámara** puede leer el topic y extraer la imagen
4. **Node-RED `read file`** como Buffer sirve el JPEG correctamente

### Arquitectura de captura funcional

```
┌─────────────────────────────────────────────┐
│ reCamera                                     │
│                                               │
│  [Sensor] → [SSCMA Supervisor] → [YOLO11]    │
│                 ↓ MQTT (localhost:1883)       │
│         topic: sscma/v0/recamera/...          │
│                 ↓                             │
│     frame-save.py (mosquitto_sub + decode)    │
│                 ↓                             │
│         /tmp/last_frame.jpg (640×640 JPEG)    │
│                 ↓                             │
│  Node-RED: GET /foto → read file → response   │
│                                               │
└──────────────────┬──────────────────────────┘
                   │ WiFi (192.168.16.1:1880)
┌──────────────────▼──────────────────────────┐
│ EdgeBox                                      │
│  curl http://192.168.16.1:1880/foto          │
│  → imagen.jpg (17 KB, 640×640)              │
└──────────────────────────────────────────────┘
```

### Comandos de control en la cámara
```bash
# Iniciar captura
echo sipedge1234* | sudo -S /etc/init.d/S95frame-capture start

# Detener captura
echo sipedge1234* | sudo -S /etc/init.d/S95frame-capture stop

# Ver estado
/etc/init.d/S95frame-capture status
```

### Scripts instalados en la cámara
- `/etc/init.d/S95frame-capture` — script de inicio/parada (arranca en boot)
- `/usr/local/bin/frame-save.py` — decodifica frame MQTT y guarda JPEG

## Node-RED en reCamera

### Concepto
Node-RED es el "backend programable" de la cámara. No hay API predefinida — tú creas los endpoints conectando nodos visualmente:
```
[http in] → [nodo lógica] → [http response]
```

### Nodos clave
| Paleta | Nodos útiles |
|--------|-------------|
| `network` | `http in`, `http response` |
| `function` | `function` (JS), `exec` (comando shell), `change` |
| `storage` | `read file`, `write file` |
| `Vision AI` | `camera`, `model`, `capture`, `stream`, `save`, `preview` |

### Lecciones duras
- `exec` con binarios grandes causa timeouts — usar `read file` en su lugar
- `context` en function nodes es por nodo (no compartido) — usar `flow.get/set` para compartir
- Los nodos `capture` y `save` son terminales (no tienen salida)
- El nodo `camera` NO emite frames — solo mensajes de estado MQTT
- httpNodeRoot `/` significa que los endpoints HTTP de Node-RED están en la raíz

### Flujo final para captura HTTP
```
[http in /foto GET] → [read file: /tmp/last_frame.jpg, Buffer] → [http response]
```
Header en http response: `Content-Type: image/jpeg`

## Escritura de archivos vía SSH multinivel
- Desde PowerShell → SSH EdgeBox → SSH reCamera: usar **base64** para evitar problemas de escaping
- `sudo` en reCamera requiere `-S` y password por stdin: `echo password | sudo -S comando`
- Si `sudo` se come el stdin, escribir primero a `/tmp/` (sin sudo) y luego `sudo cp`

## Errores de esta sesión
1. ❌ Intentar `root` para SSH → usuario correcto: `recamera`
2. ❌ Intentar `/dev/video0` con ffmpeg → no hay V4L2, usar MQTT
3. ❌ Intentar interceptar frames del nodo `camera` de Node-RED → solo emite control MQTT
4. ❌ Usar `context` en vez de `flow` → no se comparte entre nodos
5. ❌ Usar nodo `exec` para binarios JPEG → usar `read file` como Buffer
=== CONTROL DE LUZ LED ===
# Encender:
echo "eyJjb2RlIjowLCJkYXRhIjpbImxpZ2h0IiwxXSwibmFtZSI6ImxpZ2h0IiwidHlwZSI6MH0=" | base64 -d | sshpass -p 'sipedge1234*' ssh recamera@192.168.16.1 'mosquitto_pub -h localhost -t sscma/v0/recamera/node/in/89ecdff83571f71a -s'

# Apagar:
echo "eyJjb2RlIjowLCJkYXRhIjpbImxpZ2h0IiwwXSwibmFtZSI6ImxpZ2h0IiwidHlwZSI6MH0=" | base64 -d | sshpass -p 'sipedge1234*' ssh recamera@192.168.16.1 'mosquitto_pub -h localhost -t sscma/v0/recamera/node/in/89ecdff83571f71a -s'
## Sesión 2026-07-14 (continuación) — Estabilización del sistema

### ❌ El servicio de captura interfiere con el preview
El mosquitto_sub en loop continuo consumiendo frames del MQTT **compite con el pipeline
camera→model→preview**. Aunque MQTT permite múltiples suscriptores, el shell loop
con -C 1 (reconectar por cada frame) genera sobrecarga que causa:
- \"Connection lost\" intermitente en el preview
- Latencia y frames desfasados
- Posible timeout del watchdog del supervisor

**Regla**: si el preview va lento o muestra \"connection lost\", **detener la captura primero**:
sudo /etc/init.d/S95frame-capture stop

### ⏱️ YOLO tarda ~60s en cargar
El modelo YOLO11n compilado para NPU (cvimodel) necesita hasta 60 segundos para
inicializar en el chip SG2002 (RISC-V). Si se interrumpe antes (redeploy, cierre del
editor, timeout del supervisor), el modelo se destruye y hay que volver a empezar.

**Regla**: tras un reboot o deploy, esperar al menos 60s antes de verificar
que el preview funciona o que /tmp/last_frame.jpg tiene datos.

### 🔧 Usar los init scripts correctos para Node-RED
- **NO** ejecutar 
ode-red o ed.js directamente
- Usar: sudo /etc/init.d/S03node-red restart (NO S98node-red ni S9*node*)
- El binario correcto es /usr/bin/node-red-pi con flags --max-old-space-size=64 --expose-gc

### 🔗 El orden de arranque importa
1. sscma-node debe estar corriendo **antes** que Node-RED
2. Si Node-RED arranca sin sscma-node, los nodos SSCMA (camera, model) no se inicializan
3. Si sscma-node muere, los nodos se destruyen y hay que redeployar

### 🚫 No abrir el editor Node-RED mientras se despliega por API
El editor envía un deploy automático al abrirse, lo que destruye el modelo
y reinicia el ciclo de carga (otros 60s). Si hay que desplegar por API,
**cerrar todas las pestañas del editor primero**.

### 📡 La captura de imágenes depende del modelo, no de la cámara
- El nodo camera de Node-RED **NO emite frames por sus wires** — solo mensajes de control
- Los frames (JPEG base64) los publica el nodo model vía MQTT en el topic sscma/v0/recamera/node/out/<model_id>
- Sin modelo cargado (YOLO), no hay frames que capturar
