# DFW06L — Protocolo Serial de Báscula

> Documento de referencia: hallazgo del 2026-07-17.
> El manual entregado originalmente correspondía a DINI ARGEO DFWLI-2, no a DFW06L.
> Este documento captura el protocolo real verificado contra la balanza en producción.

## 1. Datos del equipo

| Parámetro | Valor |
|-----------|-------|
| **Modelo** | DINI ARGEO DFW06L |
| **Conexión** | RS485 (solo capa física, sin protocolo de direccionamiento) |
| **Dispositivo** | `/dev/ttyACM0` |
| **Baudrate** | 9600 |
| **Data bits** | 8 |
| **Paridad** | None |
| **Stop bits** | 1 |
| **Terminador** | `\r\n` (CR+LF) |

> **Importante**: No se utiliza el código de instrumento `[CC]` (p. ej. `00`) aunque
> la conexión sea RS485. Los comandos se envían sin prefijo.

## 2. Comandos

| Función | Comando | Respuesta | Estado |
|---------|---------|-----------|--------|
| Leer peso | `READ\r\n` | `ST,GS,<peso>,<unidad>` | ✅ Verificado |
| Poner cero | `ZERO\r\n` | `OK\r\n` | ✅ Verificado |
| Limpiar tara | `CLEAR\r\n` | `OK\r\n` | ✅ Verificado |
| Tarar | `TARE\r\n` | `OK\r\n` o error | ⚠️ Verificado (ERR03 con peso ≤ 0) |
| Versión | `VER\r\n` | `VER,509,DFW06L` | ✅ Verificado |
| Tara manual | `TMAN<valor>\r\n` | Pendiente de probar | ❓ No verificado |

**Comandos cortos** (según manual): `T` y `Z` como atajos para TARE y ZERO.
No probados aún.

## 3. Formato de respuesta

### Lectura de peso (`READ`)
```
ST,GS,   -0.49,kg
```

| Campo | Posición | Significado |
|-------|----------|-------------|
| `ST` | 0 | Estabilidad: `ST` = estable, `US` = inestable |
| `GS` | 1 | Bruto/Neto: `GS` = gross, `NT` = net |
| `-0.49` | 2 | Valor del peso (unidad: kg) |
| `kg` | 3 | Unidad de medida |

Ejemplo de respuesta parseada por la API:
```json
{
  "address": "00",
  "status_code": "ST",
  "is_stable": true,
  "gross_net": "GS",
  "weight": -0.49,
  "unit": "kg"
}
```

### Comandos de acción (`ZERO`, `CLEAR`, `TARE`)
```
OK
```

La respuesta `OK` indica que el comando fue **recibido**, no necesariamente
ejecutado. Por ejemplo, `TARE` responde `OK` si el comando llega bien, pero
devuelve `ERR03` si la tara no es viable (peso ≤ 0).

## 4. Códigos de error

| Código | Significado | Causa típica |
|--------|-------------|--------------|
| `ERR01` | Comando correcto + caracteres extra | `READF`, `TARES` |
| `ERR02` | Comando correcto con datos erróneos | `TAREabc` |
| `ERR03` | Comando no permitido en modo actual | TARE con peso ≤ 0, buffer ocupado |
| `ERR04` | Comando inexistente | `00REXT`, `REXT` (formato incorrecto) |

## 5. Diagnóstico rápido

```bash
# Probar comando y capturar respuesta
echo -ne "READ\r\n" > /dev/ttyACM0 && timeout 2 cat /dev/ttyACM0

# Probar zero
echo -ne "ZERO\r\n" > /dev/ttyACM0 && timeout 2 cat /dev/ttyACM0

# Monitoreo en vivo (sin comando, solo escuchar)
timeout 10 cat /dev/ttyACM0
```

> **No usar PuTTY para pruebas**: envía caracter a caracter, causando
> `ERR04` intermitente. Usar `echo -ne` desde terminal bash.

## 6. Historial

| Fecha | Evento |
|-------|--------|
| 2026-07-17 | Commands `READ`, `ZERO`, `CLEAR`, `VER` verificados en EB1 |
| 2026-07-17 | `TARE` responde `ERR03` con peso negativo (-0.49kg) — pendiente probar con peso > 0 |
| 2026-07-17 | `parse_short_response` corregido para formato DFW06L |
| 2026-07-17 | Prefijo `00` eliminado de todos los comandos en `scale.py` |
