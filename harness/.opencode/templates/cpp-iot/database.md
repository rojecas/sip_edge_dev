# Data Structures — {{PROJECT_NAME}}

> IoT/embedded projects rarely use SQL databases. If your project stores data
> (EEPROM, SPIFFS, LittleFS, JSON config), document the data structures here.
> This serves the same purpose as `docs/database.md` in other stacks:
> it's the source of truth for agents writing persistence code.
>
> Update this file manually when data structures change.
> For projects that DO use a database, replace this file with the output of
> `schema_dump.py`.

---

## Configuration (config.h / EEPROM)

```cpp
// Example: configuration stored in EEPROM
struct Config {
    char wifi_ssid[32];
    char wifi_password[64];
    uint16_t mqtt_port;
    // ...
};
```

## Sensor data format

```json
{
  "temperature": 23.5,
  "humidity": 60.0,
  "timestamp": "2026-01-01T00:00:00Z"
}
```
