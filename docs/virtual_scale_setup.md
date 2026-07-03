# Balanza Virtual DINI ARGEO DFWLI-2 — Configuración de Conexión Física

> Herramienta de desarrollo standalone para simular la balanza DINI ARGEO
> DFWLI-2 vía puerto serial desde una workstation Windows hacia el EdgeBox.

---

## 1. Componentes necesarios

| Componente | Descripción |
|---|---|
| **Workstation Windows** | PC de desarrollo con Python 3.9+ y `pyserial` instalado |
| **Cable USB–RS232** | Adaptador USB a puerto serial RS-232 (ej. Prolific PL2303, FTDI FT232) |
| **Conversor RS232/RS485** | Conversor bidireccional RS-232 a RS-485 half-duplex |
| **EdgeBox** | EdgeBox-RPI-200 con puerto RS485 (`/dev/ttyACM0`) |
| **Cableado RS485** | Par trenzado A+/B- + GND para bus RS-485 |

---

## 2. Diagrama de conexión

```
┌──────────────┐    USB      ┌──────────────┐    RS-232    ┌───────────────────┐    RS-485     ┌──────────────┐
│  Workstation  │───────────▶│ Cable USB–   │─────────────▶│ Conversor RS232/   │─────────────▶│   EdgeBox    │
│  Windows      │            │ RS232        │              │ RS485 Half-Duplex  │              │ RS485 port   │
│               │◀───────────│              │◀─────────────│                    │◀─────────────│ /dev/ttyACM0 │
└──────────────┘            └──────────────┘              └───────────────────┘              └──────────────┘
```

---

## 3. Parámetros de puerto recomendados

| Parámetro | Valor | Notas |
|---|---|---|
| **Baudrate** | 9600 | Velocidad estándar para balanza DINI ARGEO |
| **Data bits** | 8 | |
| **Paridad** | None (N) | Sin bit de paridad |
| **Stop bits** | 1 | |
| **Flow control** | None | Sin control de flujo hardware/software |

Estos parámetros deben coincidir con la configuración RS485 del EdgeBox
en `config.yaml` (sección `serial.rs485`).

---

## 4. Procedimiento de verificación de conectividad

### 4.1 Identificar el puerto COM en Windows

1. Conectar el cable USB-RS232 a la workstation.
2. Abrir **Administrador de dispositivos** (`devmgmt.msc`).
3. Expandir **Puertos (COM y LPT)**.
4. Identificar el puerto asignado (ej. `COM3`, `COM4`).

   > Si el adaptador no aparece, instalar los drivers del fabricante
   > (Prolific, FTDI, etc.).

### 4.2 Verificar conexión RS-485 en el EdgeBox

```bash
# Verificar que el puerto RS485 existe
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "ls -la /dev/ttyACM0"

# Verificar la configuración actual
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "cat /home/sipedge/sip_edge/config.yaml | grep -A5 rs485"
```

### 4.3 Probar con loopback (opcional)

Para verificar que el conversor RS232/RS485 funciona:
1. Desconectar el conversor del EdgeBox.
2. Conectar los terminales A+ y B- del conversor entre sí (loopback).
3. Ejecutar un terminal serial (ej. PuTTY, Tera Term) en el puerto COM y
   verificar que los caracteres enviados se reciben de vuelta (eco).

### 4.4 Iniciar la balanza virtual

```bash
# En la workstation Windows (PowerShell o CMD)
python src/tools/virtual_scale.py --port COM3 --dataset B

# Para ver todos los parámetros disponibles
python src/tools/virtual_scale.py --help
```

### 4.5 Verificar comunicación

Desde el EdgeBox, ejecutar un comando de prueba a través del puerto RS485:

```bash
# Verificar que el servicio SIP-Edge puede leer del RS485
ssh -i ~/.ssh/sip_edge_edgebox sipedge@192.168.1.42 "sudo journalctl -u sip-edge -f"
```

En el kiosco de pesaje, el campo de peso debería mostrar el valor actual
de la balanza virtual. También se puede enviar un comando REXT directamente:

```bash
# Desde la workstation, en otra terminal, enviar un comando REXT
# (requiere otro terminal serial o script de prueba)
echo -ne "00REXT\r\n" > /dev/ttyS0  # Linux
```

---

## 5. Comandos del REPL

Una vez iniciada la balanza virtual, el REPL interactivo acepta estas teclas
(sin necesidad de presionar Enter):

| Tecla | Acción |
|---|---|
| `n` | Avanzar a la siguiente medida/sub-paso |
| `p` | Retroceder un sub-paso |
| `w` | Override manual del peso actual |
| `g` | Saltar a una medida específica (por índice) |
| `s` | Mostrar estado actual (dataset, fila, sub-paso, peso) |
| `q` | Cerrar puerto y salir |
| `Espacio` o `d` | Simular botón PRINT (enviar lectura sin delay ni avance) |

---

## 6. Datasets disponibles

| Dataset | Característica | # Medidas |
|---|---|---|
| **A** | Contaminación baja (muestra 200–350, mineral 10–50, vegetal 2–15) | 50 |
| **B** | Contaminación media (mineral 30–120, vegetal 10–50, ~40% US) | 50 |
| **C** | Alta contaminación con tendencia creciente | 50 |
| **D** | Outliers ocasionales en mineral y vegetal | 50 |
| **E** | Aleatoria uniforme dentro de rangos típicos | 50 |

Para re-generar los datasets (por ejemplo, con una semilla diferente):

```bash
python scripts/generate_readings.py --seed 123
```

---

## 7. Solución de problemas

| Problema | Causa probable | Solución |
|---|---|---|
| `ERROR: No se pudo abrir el puerto serial` | Puerto COM no existe o está ocupado | Verificar en Administrador de dispositivos; cerrar otros programas que usen el puerto |
| `ERROR: Dataset no encontrado` | El CSV no existe en `data/readings/` | Ejecutar `python scripts/generate_readings.py` primero |
| El EdgeBox no recibe datos | Cableado RS-485 invertido (A+/B- cruzados) | Intercambiar los cables A+ y B- en el conversor |
| El EdgeBox recibe datos corruptos | Baudrate o parámetros no coinciden | Verificar que ambos extremos usen 9600-8-N-1 |
| `ImportError: No module named 'serial'` | pyserial no instalado | `pip install pyserial` |
