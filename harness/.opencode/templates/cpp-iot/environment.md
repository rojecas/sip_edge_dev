# Environment — {{PROJECT_NAME}}

> El agente DEBE leer este archivo **antes de ejecutar cualquier comando bash**.
> Describe DONDE y COMO se ejecutan los comandos, y que servicios estan disponibles.
> init.ps1 auto-detecta el contexto (Docker vs nativo) y avisa si hay discrepancias.

## Execution mode

**Mode:** native

No se detecto Docker. Todos los comandos se ejecutan directamente en el host.
Si usas Docker, cambia el modo a `docker` y completa la seccion correspondiente.

## Shell

Todos los comandos usan el shell del sistema. Sin prefijo de contenedor.

## Runtime

- Python 3.9+ (para PlatformIO CLI)
- PlatformIO CLI (disponible como `pio`)
- Sin aislamiento por contenedor

## Services

Ninguno detectado. IoT projects generalmente no usan servicios de BD.
Si usas MQTT broker u otros servicios en red, agregalos aqui.

Ejemplo:
| Service | Host access | Container access |
|---------|------------|------------------|
| Mosquitto MQTT | 127.0.0.1:1883 | mosquitto:1883 |

## Hardware requerido

- ESP32 Dev Board (o similar) en puerto COM3
- Si usas multiples placas, definirlas todas aqui con su puerto/env

## Init / Lifecycle

```bash
# Verificar entorno
./init.ps1

# Compilar firmware
pio run

# Subir firmware al dispositivo
pio run -t upload

# Monitor serial
pio device monitor

# Ejecutar tests en host
pio test -e native
```
