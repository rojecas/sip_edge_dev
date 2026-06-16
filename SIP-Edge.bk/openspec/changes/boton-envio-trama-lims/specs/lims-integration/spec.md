## ADDED Requirements

### Requirement: Construcción de trama LIMS
El sistema SHALL construir una trama CSV con los datos del pesaje en el siguiente orden de campos:

`Id,Fecha,Hora,Vagon,Guia,PesoMuestra,0,0,0,0,0,0,0,PesoVegetal,PesoMineral`

Donde:
- `Id`: Número entero autoincremental
- `Fecha`: Fecha del pesaje en formato YYYY-MM-DD
- `Hora`: Hora del pesaje en formato HH:MM:SS
- `Vagon`: Identificador alfanumérico del vagón
- `Guia`: Código alfanumérico de guía
- `PesoMuestra`: Peso de la muestra en kg con 2 decimales
- `0` (x7): Campos reservados legacy, siempre 0
- `PesoVegetal`: Peso vegetal en kg con 2 decimales
- `PesoMineral`: Peso mineral en kg con 2 decimales

#### Scenario: Trama construida correctamente
- **WHEN** el operador presiona "Enviar a LIMS" con todos los datos del pesaje completos
- **THEN** el sistema construye la trama en el formato definido, por ejemplo: `66,2025-11-27,15:00:44,PQR321,1,17.08,0,0,0,0,0,0,0,8.40,6.81`

### Requirement: Envío de trama por RS-232
El sistema SHALL enviar la trama construida a través de un puerto RS-232 independiente hacia el sistema LIMS.

#### Scenario: Envío exitoso a LIMS
- **WHEN** el sistema construye la trama y el puerto RS-232 está disponible
- **THEN** el sistema envía la trama por el puerto serial y muestra feedback visual de éxito en la UI

#### Scenario: Puerto RS-232 no disponible
- **WHEN** el sistema intenta enviar la trama pero el puerto RS-232 no responde
- **THEN** el sistema muestra error "Error de comunicación con LIMS" y permite reintentar

### Requirement: Configuración de puerto LIMS
El sistema SHALL permitir al Administrador configurar el puerto RS-232 para LIMS (ruta, baudrate, paridad) en la interfaz de configuración, independiente de la configuración de la báscula.

#### Scenario: Admin configura puerto LIMS
- **WHEN** un Administrador modifica los parámetros del puerto RS-232 para LIMS
- **THEN** el sistema guarda en `config.yaml` y aplica en el próximo envío
