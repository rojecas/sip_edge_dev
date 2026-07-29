# Configuracion de SMSC para Quectel EC25

> Como consultar y cambiar el Centro de Mensajes SMS (SMSC) en el modem Quectel EC25.

## Requisitos previos

El puerto serial `/dev/ttyUSB2` esta gestionado por ModemManager. Para enviar comandos AT directamente, hay que detener ModemManager temporalmente y el servicio sip-edge (cuyo polling de SMS tambien usa el puerto via ModemManager).

## Procedimiento

### 1. Detener servicios

```bash
sudo systemctl stop sip-edge
sudo systemctl stop ModemManager
sleep 2
```

### 2. Ejecutar script Python de cambio de SMSC

Script: `/home/sipedge/sip_edge/scripts/set_smsc.py` (crear si no existe).

```python
import serial, time

SMSC = "+573003690025"  # cambiar segun operador

s = serial.Serial("/dev/ttyUSB2", 115200, timeout=3)
time.sleep(0.5)

# Consultar SMSC actual
s.write(b"AT+CSCA?\r\n")
time.sleep(0.5)
print("Actual:", s.read(200).decode().strip())

# Cambiar SMSC
s.write(f"AT+CSCA=\"{SMSC}\",145\r\n".encode())
time.sleep(0.5)
print("Set:", s.read(200).decode().strip())

# Verificar
s.write(b"AT+CSCA?\r\n")
time.sleep(0.5)
print("Verificar:", s.read(200).decode().strip())

s.close()
```

Ejecutar:
```bash
source /home/sipedge/sip_edge/venv/bin/activate
python3 /home/sipedge/sip_edge/scripts/set_smsc.py
```

### 3. Reiniciar servicios

```bash
sudo systemctl start ModemManager
sleep 8
sudo systemctl start sip-edge
```

## Numeros SMSC por operador (Colombia)

| Operador | SMSC |
|----------|------|
| **Tigo** | `+573003690025` (original de la SIM) |
| **Tigo** | `+573006690031` (reportado por SMS de saldo) |
| **Tigo** | `+573000000002` (prueba) |

> **Nota:** El SMSC correcto puede variar segun la SIM y la region. Para obtener el SMSC real, solicitar saldo con `*10#` via USSD y leer el campo `smsc` del SMS de respuesta de Tigo.

## Comando AT de referencia

| Comando | Descripcion |
|---------|------------|
| `AT+CSCA?` | Consultar SMSC actual |
| `AT+CSCA="+57XXXXXXXXXX",145` | Cambiar SMSC |
| `AT+CMGF=1` | Modo texto (necesario para enviar SMS) |

## Referencia

- Manual AT del Quectel EC25: `AT+CSCA` (Service Center Address)
- Documento de configuracion de hardware: `docs/Informe 01 - Configuracion de Hardware.md`
- Comandos ModemManager: `docs/Comandos de ModemManager para Quectel EC25.md`
