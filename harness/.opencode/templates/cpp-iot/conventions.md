# Convenciones de codigo

> Homogeneidad extrema. La IA predice mejor cuando el repositorio se parece
> a si mismo en todas partes.

## Estilo C++

- **Estándar:** C++17 (ESP32), C++11 (AVR minimo).
- **Formato:** clang-format con estilo LLVM modificado (4 espacios, ColumnLimit 100).
  Config en `.clang-format` en la raiz del proyecto.
- **Extensiones:** `.h` para headers, `.cpp` para implementacion.
- **Strings:** `std::string` en ESP32, `const char*` o `char[]` en AVR.
  NUNCA la clase `String` de Arduino.

## Nombres

| Tipo                   | Convencion       | Ejemplo                        |
|------------------------|------------------|--------------------------------|
| Archivos               | `snake_case`     | `dht_sensor.h`, `mqtt_client.cpp` |
| Clases / Structs       | `PascalCase`     | `DhtSensor`, `MqttConfig`      |
| Funciones / metodos    | `camelCase`      | `readTemperature`, `connect`   |
| Enums                  | `PascalCase`     | `SensorStatus`                 |
| Constantes             | `kPascalCase`    | `kDefaultMqttPort`             |
| Macros / defines       | `UPPER_SNAKE`    | `MQTT_MAX_PACKET_SIZE`         |
| Pines                  | `UPPER_SNAKE`    | `DHT_PIN`, `LED_BUILTIN`       |
| Variables miembro      | `_camelCase`     | `_lastReadTime`, `_isConnected` |

## Estructura de proyecto (PlatformIO)

```
{{PROJECT_NAME}}/
  platformio.ini
  src/
    main.cpp
  include/
    config.h
  lib/
  test/
    test_<module>/
      test_<module>.cpp
```

## Reglas de modulos

Cada modulo en `lib/<name>/` o `src/modules/<name>/`:

```cpp
// <name>.h
#pragma once   // NUNCA #ifndef guards

#include <Arduino.h>   // solo si es necesario

enum class <Name>Status { Ok, Timeout, NotConnected, InvalidData };

class <Name> {
public:
    <Name>(uint8_t pin1, uint8_t pin2 = 0);
    bool begin();                             // retorna false si no inicializa
    <Name>Status read(float& outValue);       // retorna Status
private:
    uint8_t _pin1;
    uint8_t _pin2;
    unsigned long _lastReadMs;
};
```

- `#pragma once` siempre. Nunca include guards manuales.
- Constructor recibe pines y configuracion. `begin()` inicializa hardware.
- Funciones `read()` / `write()` retornan `Status`, valor por referencia.
- Sin `Serial.print()` dentro de modulos. Usar un sistema de logging externo o `printf` condicional con `#ifdef DEBUG`.
- `unsigned long` para marcas de tiempo (`millis()`).

## Tests (Unity)

Cada modulo tiene su test en `test/test_<module>/test_<module>.cpp`:

```cpp
#include <unity.h>
#include "<module>.h"

void setUp(void) { /* corre antes de cada test */ }
void tearDown(void) { /* corre despues de cada test */ }

void test_<module>_<metodo>_<escenario>() {
    // Arrange
    <Module> m(pin);
    // Act
    auto status = m.begin();
    // Assert
    TEST_ASSERT_TRUE(status);
}

void loop() {}  // PlatformIO Unity requiere esto

int main() {
    UNITY_BEGIN();
    RUN_TEST(test_<module>_<metodo>_<escenario>);
    return UNITY_END();
}
```
