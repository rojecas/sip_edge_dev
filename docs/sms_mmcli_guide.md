# Guia de Envio de SMS con ModemManager (mmcli) en Quectel EC25

> Hallazgos verificados durante pruebas de conectividad (2026-07-03)
> Modem: Quectel EC25, Operador: TIGO Colombia, Hardware: EdgeBox-RPI-200

## 1. Sintaxis correcta de mmcli para crear SMS

### INCORRECTO (NO funciona)

```bash
mmcli -m 0 --messaging-create-sms="number='+573001234567',text='mensaje'"
```

### CORRECTO (funciona)

```bash
mmcli -m 0 --messaging-create-sms "number='+573001234567',text='mensaje'"
```

**Diferencia critica:** El flag `--messaging-create-sms` y las propiedades deben ser DOS argumentos separados (sin el signo `=`). Esta es la sintaxis que usa internamente sip-edge (`sms_service.py`) y la unica que entrega el SMS exitosamente.

Si se usa `--messaging-create-sms="..."` (con `=`), mmcli reporta "successfully sent" pero el mensaje nunca llega al destinatario (el SMSC queda vacio en el mensaje).

## 2. SMSC (Centro de Mensajes SMS) - Obligatorio

mmcli NO utiliza el SMSC almacenado en la memoria del modem a menos que se especifique explicitamente en las propiedades del SMS.

### Verificar SMSC de un SMS enviado

```bash
mmcli -s <ID> --output-keyvalue | grep smsc
```

Si el campo `smsc` aparece como `--` (vacio), el SMS fue marcado como "sent" pero nunca se encamino a traves del centro de mensajes de la operadora y nunca llegara al destinatario.

### SMSC verificado para TIGO Colombia

| SMSC | Estado | Notas |
|------|--------|-------|
| `+573003690025` | **FUNCIONAL** | Verificado el 2026-07-03. Envio exitoso. |
| `+573006690031` | No verificado | Reportado por SMS de saldo segun documentacion previa |
| `+573000000002` | No verificado | Usado en pruebas previas |

### Envio CORRECTO con SMSC explicito

```bash
mmcli -m 0 --messaging-create-sms "number='+573001234567',text='mensaje',smsc='+573003690025'"
mmcli -s <ID> --send
```

## 3. Codificacion y saltos de linea

Los scripts Bash que envian SMS deben usar **saltos de linea Unix (LF, \n)**, no Windows (CRLF, \r\n). Un archivo con CRLF produce el error:

```
syntax error: unexpected end of file
```

aunque el contenido sea sintacticamente correcto. Para convertir:

```bash
sed -i 's/\r$//' nombre_del_script.sh
```

## 4. Diagnostico de problemas de envio

### Paso 1: Verificar estado del modem

```bash
mmcli -m 0 | grep -E "state|signal quality|operator name"
# Debe mostrar: state: connected, senal > 20%, operador: TIGO
```

### Paso 2: Verificar SMSC del SMS enviado

```bash
# Despues de enviar, listar IDs
mmcli -m 0 --messaging-list-sms
# Verificar SMSC
mmcli -s <ID> --output-keyvalue | grep smsc
# Si aparece '--', el SMS no llegara
```

### Paso 3: Revisar logs de ModemManager

```bash
sudo journalctl -u ModemManager --no-pager -n 50 | grep -i sms
```

## 5. Comparativa: send_sms.sh antes vs despues

| Aspecto | Version anterior | Version reparada |
|---------|-----------------|-----------------|
| Sintaxis del flag | `--messaging-create-sms="..."` | `--messaging-create-sms "..."` |
| SMSC | No incluido | Incluido: `smsc='+573003690025'` |
| Modo sudo | `sudo` (requiere terminal) | `sudo -n` (non-interactive) |
| Resultado | "Sent" pero no llega | Llega al destinatario |

## 6. Flujo completo de envio correcto (3 pasos)

```bash
# 1. Crear SMS con SMSC explicito (props como argumento separado)
SMS_PATH=$(sudo mmcli -m 0 --messaging-create-sms "number='+573001234567',text='Hola',smsc='+573003690025'" 2>&1)
SMS_ID=$(echo "$SMS_PATH" | grep -oP '/org/freedesktop/ModemManager1/SMS/\K[0-9]+')

# 2. Enviar
sudo mmcli -s "$SMS_ID" --send

# 3. Verificar SMSC
sudo mmcli -s "$SMS_ID" --output-keyvalue | grep smsc
```

## 7. Script send_sms.sh reparado

El script en `/usr/local/bin/send_sms.sh` fue actualizado con ambos fixes:
- Usa `--messaging-create-sms "props"` (sin `=`)
- Incluye `smsc='+573003690025'` en las propiedades

## Referencias

- `docs/Configuracion de SMSC para Quectel EC25.md` - SMSC y comandos AT
- `docs/Comandos de ModemManager para Quectel EC25.md` - Comandos mmcli basicos
- `src/sms_service.py` - Implementacion de referencia en sip-edge
- `/usr/local/bin/send_sms.sh` - Script de envio reparado


## 8. Hallazgo: Fechas con barra / bloqueadas por Tigo (2026-07-05)

### Problema
Los SMS que contenian fechas en formato `24/06/2026` (dd/mm/aaaa) NO eran
entregados por Tigo Colombia. Mensajes con texto similar pero SIN barras
si llegaban correctamente.

### Sintoma
Inconsistencia intermitente: algunas respuestas del asistente AI llegaban
y otras no. El patron era que las respuestas con fechas numericas (con /)
nunca llegaban.

### Causa raiz
Tigo bloquea los SMS que contienen secuencias tipo fecha con barras,
probablemente por filtros anti-spam que interpretan el patron como numero
de telefono mal formateado.

### Fix (2026-07-06)
Se modifico el SYSTEM_PROMPT del LLM en src/agent_orchestrator.py para
que use formato "24 jun 2026" (con mes en texto) en vez de "24/06/2026".

### Prueba
- Enviar SMS con "24/06/2026" -> NO llega
- Enviar SMS con "24 jun 2026" -> LLEGA
- Enviar SMS con solo "/" -> LLEGA (la barra sola no es bloqueada)

### Referencia
Documento completo: harness/docs/findings/sms_date_format_bug.md
