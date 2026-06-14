# Resumen de Comandos de ModemManager para Quectel EC25

## Comandos Básicos

### Ver estado del módem
```bash
# Listar módems disponibles
mmcli -L

# Ver estado completo del módem
mmcli -m 0

# Ver información resumida
mmcli -m 0 --output-keyvalue
```

### Información específica
```bash
# Ver calidad de señal
mmcli -m 0 | grep "signal quality"

# Ver operador de red
mmcli -m 0 | grep "operator name"

# Ver estado de conexión
mmcli -m 0 | grep "state"

# Ver información de la SIM
mmcli -m 0 | grep -A 10 "SIM"

# Ver capacidades del módem
mmcli -m 0 | grep -A 20 "Modes"
```

## Control del Módem

### Encender/apagar
```bash
# Encender módem
mmcli -m 0 --enable

# Apagar módem
mmcli -m 0 --disable

# Reiniciar módem
mmcli -m 0 --reset

# Encender radio (forzar conexión)
mmcli -m 0 --set-power-state-on
```

### Configuración de red
```bash
# Establecer modo de red (2G, 3G, 4G)
mmcli -m 0 --set-allowed-modes="3g|4g"

# Establecer banda preferida
mmcli -m 0 --set-preferred-mode="lte"
```

## Comandos SMS

### Enviar SMS
```bash
# Crear un SMS (devuelve ID)
mmcli -m 0 --messaging-create-sms="number='+573001234567',text='Mensaje de prueba'"

# Enviar SMS por ID
mmcli -s 1 --send
```

### Gestionar SMS
```bash
# Listar todos los SMS
mmcli -m 0 --messaging-list-sms

# Ver contenido de un SMS
mmcli -s 1

# Eliminar un SMS
mmcli -s 1 --delete

# Eliminar todos los SMS
for i in $(mmcli -m 0 --messaging-list-sms | grep -oP '/SMS/\K\d+'); do
    mmcli -s $i --delete
done
```

### Configuración SMS
```bash
# Ver configuración de mensajería
mmcli -m 0 | grep -A 10 "Messaging"

# Establecer centro de mensajes (SMSC)
mmcli -m 0 --messaging-set-default-smsc="+573006000000"
```

## Comandos de Red

### Bearer (conexión de datos)
```bash
# Listar bearers activos
mmcli -L --bearers

# Ver detalles del bearer
mmcli -b 1

# Crear nuevo bearer con APN
mmcli -m 0 --create-bearer="apn=internet.tigo.com.co"

# Activar bearer
mmcli -b 1 --enable

# Desactivar bearer
mmcli -b 1 --disable
```

### Información de red
```bash
# Ver IP asignada
mmcli -b 1 | grep "address"

# Ver DNS
mmcli -b 1 | grep "dns"

# Ver estadísticas de datos
mmcli -b 1 | grep -A 10 "Statistics"
```

## Comandos AT (avanzado)

### Enviar comandos AT directos
```bash
# Enviar comando AT simple
mmcli -m 0 --command="AT+CSQ"

# Ver información de la SIM
mmcli -m 0 --command="AT+CPIN?"

# Ver registro en red
mmcli -m 0 --command="AT+CREG?"

# Ver operador
mmcli -m 0 --command="AT+COPS?"

# Ver IMEI
mmcli -m 0 --command="AT+CGSN"
```

## Monitoreo en Tiempo Real

### Ver logs del sistema
```bash
# Monitorear logs de ModemManager
sudo journalctl -u ModemManager -f

# Ver logs recientes
sudo journalctl -u ModemManager -n 50

# Ver logs del kernel relacionados con módem
dmesg | grep -i "quectel\|option\|ttyUSB"
```

### Monitorear SMS entrantes
```bash
# Modo watch (detecta SMS nuevos)
mmcli -m 0 --messaging-list-sms --watch
```

## Solución de Problemas

### Reiniciar servicios
```bash
# Reiniciar ModemManager
sudo systemctl restart ModemManager

# Reiniciar NetworkManager
sudo systemctl restart NetworkManager
```

### Forzar detección de módem
```bash
# Detener ModemManager
sudo systemctl stop ModemManager

# Recargar drivers USB
sudo modprobe -r option qmi_wwan
sudo modprobe option qmi_wwan

# Iniciar ModemManager
sudo systemctl start ModemManager
```

### Verificar permisos
```bash
# Ver grupo del usuario
groups

# Agregar usuario al grupo dialout (si es necesario)
sudo usermod -a -G dialout $USER
```

## Comandos Útiles Adicionales

### Resumen rápido del estado
```bash
# Función para mostrar estado rápido
status_4g() {
    echo "=== MÓDULO 4G ==="
    mmcli -m 0 2>/dev/null | grep -E "state|signal quality|operator name"
    echo ""
    echo "=== IP ==="
    ip addr show wwan0 2>/dev/null | grep inet
    echo ""
    echo "=== RUTA ==="
    ip route | grep default | grep wwan0
}
```

### Exportar información completa
```bash
# Guardar diagnóstico en archivo
mmcli -m 0 --output-keyvalue > modem_status.txt
mmcli -b 1 --output-keyvalue >> modem_status.txt
```

## Referencia Rápida

| Acción | Comando |
|--------|---------|
| Ver módem | `mmcli -L` |
| Estado general | `mmcli -m 0` |
| Calidad señal | `mmcli -m 0 \| grep signal` |
| Enviar SMS | `mmcli -m 0 --messaging-create-sms` |
| Listar SMS | `mmcli -m 0 --messaging-list-sms` |
| Ver IP | `mmcli -b 1 \| grep address` |
| Reiniciar módem | `mmcli -m 0 --reset` |
| Comando AT | `mmcli -m 0 --command="AT+CSQ"` |

---

## Ejemplo: Script de estado completo

```bash
#!/bin/bash
# Script: 4g_status.sh
echo "═══════════════════════════════════════"
echo "     ESTADO DEL MÓDULO 4G"
echo "═══════════════════════════════════════"

# Módem
if mmcli -L 2>/dev/null | grep -q Modem; then
    echo "✅ Módem detectado"
    STATE=$(mmcli -m 0 | grep "state:" | head -1 | awk '{print $2}')
    echo "   Estado: $STATE"
    
    SIGNAL=$(mmcli -m 0 | grep "signal quality" | awk '{print $3}')
    echo "   Señal: $SIGNAL"
    
    OPERATOR=$(mmcli -m 0 | grep "operator name" | awk -F': ' '{print $2}')
    echo "   Operador: $OPERATOR"
else
    echo "❌ Módem no detectado"
fi

echo ""
echo "═══════════════════════════════════════"
echo "     CONEXIÓN DE DATOS"
echo "═══════════════════════════════════════"

if ip addr show wwan0 2>/dev/null | grep -q inet; then
    IP=$(ip addr show wwan0 | grep "inet " | awk '{print $2}')
    echo "✅ Conexión activa"
    echo "   IP: $IP"
else
    echo "❌ Sin conexión de datos"
fi
```