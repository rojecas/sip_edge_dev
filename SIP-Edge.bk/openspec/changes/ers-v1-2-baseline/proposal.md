## Why

Establecer la línea base oficial del proyecto SIP-Edge incorporando la Especificación de Requisitos de Software (ERS) V1.2 como spec formal de OpenSpec. Este documento, elaborado bajo estándar IEEE 29148, define el alcance del MVP y los requisitos diferidos a futuro.

## What Changes

- Incorporar el ERS V1.2 completo como specs de OpenSpec, estructurado por módulos/capabilities
- Establecer la trazabilidad entre requisitos funcionales (RF-001 a RF-021) y no funcionales (RNF-001 a RNF-008)
- Documentar el Anexo F (Future Scope) como referencia de requisitos diferidos
- No hay cambios sobre código existente — es la creación de la especificación base

## Capabilities

### New Capabilities

- `user-auth`: Autenticación por credenciales (bcrypt), RBAC con roles Operador/Corresponsal/Administrador (RF-001, RF-002, RF-021)
- `weighing-scale`: Interacción bidireccional con báscula serial RS232/USB, comando-respuesta con timeout configurable (RF-003)
- `data-persistence`: Persistencia en MariaDB con integridad transaccional, gestión de haciendas y suertes en cascada (RF-004 a RF-008)
- `ai-agent`: Orquestador con Qwen 2.5 3B, detección de anomalías estadísticas (Z-score >3), análisis SQL con Function Calling (RF-009 a RF-011)
- `sms-notification`: Envío SMS vía GSM (comandos AT), reportes programados y alertas de seguridad (RF-012 a RF-014)
- `admin-config`: Configuración dinámica de puertos, persistencia en config.yaml, respaldos automáticos, modo manual de emergencia (RF-015 a RF-020)
- `ui-kiosk`: Interfaz de kiosko con feedback visual por colores, pesos readonly, cascada hacienda-suerte (requisitos de UI distribuidos)
- `offline-operations`: Operación 100% offline, recuperación ante fallos con systemd, watchdog (RNF-002, RNF-003)

### Modified Capabilities

Ninguna — es la baseline inicial.

## Impact

- Creación de specs en `openspec/specs/` para cada capability
- El ERS V1.2 existente en `docs/` se mantiene como documento fuente; los specs de OpenSpec serán la representación estructurada para el flujo de trabajo
- El código Python actual (`src/tools.py`, `src/agent.py`, `main.py`) no se modifica en este cambio
