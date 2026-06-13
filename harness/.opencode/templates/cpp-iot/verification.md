# Verificacion — Como demostrar que el trabajo funciona

> Regla de oro: **el agente no dice "funciona", lo demuestra**.
> Toda feature termina con evidencia ejecutable, no con afirmaciones.
> En hardware, "funciona" significa compila + tests pasan + no rompe otras features.

## Niveles de verificacion

### Nivel 1 — Compilacion para todos los targets (obligatorio)

Toda feature nueva debe compilar sin errores ni warnings para cada
`[env]` definido en `platformio.ini`.

```bash
pio run           # compila para el env por defecto
pio run -e esp32dev -e native
```

Si la feature introduce codigo especifico de plataforma, usa `#ifdef`:
```cpp
#ifdef ESP32
    // codigo especifico
#endif
```

### Nivel 2 — Tests unitarios en host (obligatorio para modulos nuevos)

Todo modulo (`lib/` o `src/modules/`) tiene al menos un test que:

1. Cubre el camino feliz (lectura/escritura exitosa).
2. Cubre todos los caminos de error que el modulo puede producir (timeout, datos invalidos, sensor no conectado, valores fuera de rango, overflow). Si un modulo puede fallar de N formas, hay N tests.

```bash
pio test -e native           # tests en host (sin hardware)
pio test -e esp32dev          # tests on-device (si aplica)
```

### Nivel 3 — Tests on-device (obligatorio para features de hardware)

Las features que tocan GPIO, ADC, Wi-Fi, BLE, o pantallas requieren
al menos un test on-device en el target fisico real. Si no tienes
el hardware conectado durante CI, marca el test como `[hw]` y
documentalo.

```cpp
TEST_CASE("LED se enciende al llamar turnOn", "[hw]") {
    Led led(LED_BUILTIN);
    led.turnOn();
    TEST_ASSERT_EQUAL(HIGH, digitalRead(LED_BUILTIN));
}
```

### Nivel 4 — Verificacion de memoria (ESP32)

Para features que tocan strings, buffers, o JSON:

```bash
pio run -e esp32dev -t size    # revisa RAM/Flash usada
```

Si una feature consume mas de 10% adicional de RAM o Flash, justificar en el spec.

### Nivel 5 — Verificacion del harness

Antes de declarar `done`:
```bash
./init.ps1
```
Debe terminar con exit code 0 y todos los bloques [OK].
