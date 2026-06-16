## Why

El laboratorio debe enviar los datos de cada pesaje a un sistema LIMS (Laboratory Information Management System) especializado en agroindustria. Se necesita un botón en la UI del kiosko que, al presionarse, construya y envíe una trama estructurada por un puerto RS-232 independiente. El botón debe permanecer deshabilitado hasta que todos los campos obligatorios del formulario de pesaje estén completos.

## What Changes

- **NEW** capability `lims-integration`: Envío de trama serial RS-232 a sistema LIMS con la estructura de datos del pesaje
- **MODIFIED** capability `ui-kiosk`: Agregar botón "Enviar a LIMS" en formulario de pesaje, habilitado solo cuando todos los datos obligatorios estén completos
- Agregar configuración de puerto RS-232 para LIMS en interfaz Admin

## Capabilities

### New Capabilities

- `lims-integration`: Construcción y envío de trama serial RS-232 hacia sistema LIMS con los datos del pesaje (Id, Fecha, Hora, Vagon, Guía, Pesos), más la gestión de configuración del puerto

### Modified Capabilities

- `ui-kiosk`: Agregar botón "Enviar a LIMS" en formulario de pesaje, con validación de completitud de datos y feedback visual de envío

## Impact

- Hardware: Nuevo puerto RS-232 (independiente del RS-485 de báscula) para comunicación con LIMS
- UI: Nuevo botón + lógica de habilitación condicional en formulario de pesaje
- Backend: Nuevo driver serial RS-232 para salida de datos, endpoint para construir y enviar trama
- Configuración: Agregar puerto, baudrate y parámetros RS-232 para LIMS en `config.yaml`
