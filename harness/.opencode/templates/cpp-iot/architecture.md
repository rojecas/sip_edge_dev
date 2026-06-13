# Arquitectura — Que significa "hacer un buen trabajo"

> Este documento define el estandar de calidad. Los agentes revisores
> evaluan codigo contra este archivo. Si no esta aqui, no es un requisito.

## Hardware objetivo

El proyecto compila y ejecuta en una o mas de estas plataformas:
- **ESP32 / ESP32-S3** (Xtensa o RISC-V, Wi-Fi + BLE, PlatformIO).
- **Arduino Uno / Mega** (AVR, sin OS, RAM ~2KB-8KB).
- **ESP8266** (legado, solo si es requisito explicito).

El target se define en `platformio.ini` bajo un `[env]` por placa.
Las features nuevas DEBEN compilar para todas las env activas.

## Principios

1. **Capas minimas.** El firmware tiene exactamente estas capas:
   - `main.cpp` — `setup()` y `loop()` (o equivalente RTOS). Solo orquesta.
   - `modules/<name>/<name>.h` + `<name>.cpp` — logica de un sensor, actuador, protocolo o pantalla.
   - `lib/<name>/` — wrappers de librerias externas (solo si es necesario aislar la dependencia).
   No introducir capas adicionales sin una razon documentada en `feature_list.json`.

2. **Responsabilidad unica por modulo.** Un modulo = un sensor, un actuador, un protocolo (MQTT, HTTP), o una pantalla. Si un `.cpp` supera las 300 lineas, dividirlo.

3. **No bloquear el loop.** `loop()` debe ejecutarse sin delays bloqueantes.
   Usar `millis()` para temporizacion no bloqueante. Si la plataforma lo soporta, usar FreeRTOS tasks.

4. **Manejo de errores defensivo.** Todo sensor/actuador puede fallar (sin conexion, timeout, valor fuera de rango). Las funciones publicas devuelven un `enum class Status` o similar. No `while(true)` ni `delay()` infinitos esperando hardware.

5. **Memoria controlada.** En AVR, evitar `String` (usar `char[]`). En ESP32, preferir `std::string` sobre `String`. Sin `new`/`delete` en `loop()`. Sin `malloc` libre.

## Flujo de datos

```
Sensor/Entrada → modulo (lectura + filtro) → logica (main.cpp) → modulo (actuador/salida/pantalla)
                                       ↕
                              comunicacion (MQTT, HTTP, Serial)
```

- `main.cpp` solo cablea modulos: lee sensor, decide, escribe actuador.
- Los modulos no conocen otros modulos. Si dos modulos necesitan comunicarse, se hace via `main.cpp`.
- La comunicacion (Wi-Fi, MQTT) se inicializa en `setup()` y se maneja en `loop()`.

## Tests (PlatformIO)

- Tests unitarios en `test/` usando Unity (platformio test).
- Tests nativos en host (`pio test -e native`) cuando no requieren hardware real.
- Tests on-device (`pio test -e esp32dev`) para features que tocan GPIO, Wi-Fi o perifericos.
- Mockear `Serial`, `Wire`, y `WiFi` cuando sea necesario para tests en host.
