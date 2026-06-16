## Why

El fabricante de la báscula industrial confirmó que el puerto de comunicación es RS-485, no RS-232 como se especificaba originalmente en el ERS V1.2. RS-485 es un estándar industrial diferente que requiere un adaptador USB-RS485 y cambios en la configuración de comunicación (half-duplex, terminación, direccionamiento). Este cambio alinea la especificación con el hardware real disponible.

## What Changes

- **MODIFIED** capability `weighing-scale`: Cambiar protocolo de comunicación de RS-232 a RS-485
- Cambiar referencia de hardware en toda la especificación: RS-232 → RS-485
- Agregar requisitos de configuración específicos de RS-485 (half-duplex, terminación, direccionamiento)

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `weighing-scale`: Cambiar interfaz de hardware de RS-232 a RS-485, incluyendo adaptador USB-RS485, modo half-duplex, configuración de terminación y direccionamiento de dispositivos

## Impact

- Hardware: Reemplazar adaptador USB-RS232 por adaptador USB-RS485
- Código: El driver serial debe soportar modo half-duplex (control de dirección TX/RX mediante pin RTS o GPIO)
- Configuración: Agregar campos de terminación y dirección de dispositivo en `config.yaml` e interfaz Admin
- Documentación: Actualizar ERS, esquemas de conexión y guías de instalación
