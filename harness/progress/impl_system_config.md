# Implementacion — system_config

- **Feature:** system_config (id: 1)
- **Fecha:** 2026-06-13
- **Agente:** implementer
- **Estado:** implementacion completa, esperando reviewer

## Archivos modificados

| Archivo | Accion | Descripcion |
|---------|--------|-------------|
| `src/config.py` | CREADO | Modelo de dominio: dataclasses congelados, load/save/validate |
| `src/main.py` | MODIFICADO | Endpoints GET/PUT /api/config, POST /api/config/test/{port}, lifespan |
| `tests/test_config.py` | CREADO | 20 tests unitarios y de integracion |
| `requirements.txt` | MODIFICADO | Agregados pyserial==3.5 y httpx==0.28.1 |

## Trazabilidad

| Requirement | Test(s) |
|------------|---------|
| R1 | `test_get_config_returns_200` |
| R2 | `test_put_config_valid_returns_200` |
| R3 | `test_load_defaults_when_no_file`, `test_save_and_load_roundtrip`, `test_load_invalid_yaml_fallback` |
| R4 | `test_load_defaults_when_no_file`, `test_creation_defaults`, `test_immutability`, `default_config()` |
| R5 | `test_invalid_baudrate`, `test_put_config_invalid_baudrate_returns_422` |
| R6 | `test_invalid_data_bits` |
| R7 | `test_invalid_parity` |
| R8 | `test_invalid_stop_bits` |
| R9 | `test_invalid_modem_index` |
| R10 | `test_test_rs485_serial_attempt` |
| R11 | `test_test_rs232_serial_attempt` |
| R12 | `test_test_gsm_mmcli_success`, `test_test_gsm_mmcli_failure` |
| R13 | `test_test_invalid_port_returns_404` |
| R14 | `test_creation_defaults`, `test_immutability` |
| R15 | `test_atomic_write_does_not_corrupt` |
| R16 | `test_load_invalid_yaml_fallback` |

## Decisiones tecnicas

1. **Lifespan en lugar de on_event:** FastAPI 0.115.6 depreca `@app.on_event("startup")`. Se uso `@asynccontextmanager` + `lifespan=` para cargar la configuracion al arranque.
2. **Import condicional de `serial`:** `pyserial` se importa dentro de los endpoints de test (`/api/config/test/{port}`), no a nivel de modulo. Esto evita dependencias circulares y sigue el patron de principio de arquitectura: dependencias de conectividad solo en capa de endpoints.
3. **Atomicidad YAML:** `save_config()` usa `tempfile.mkstemp()` + `os.replace()`, no `yaml.dump()` directo sobre el archivo destino.
4. **httpx para TestClient:** FastAPI `TestClient` requiere `httpx`. Se agrego `httpx==0.28.1` a `requirements.txt` como dependencia de test (no de produccion).

## Verificacion

```bash
docker compose exec backend python -m unittest discover -s tests -v
# Ran 20 tests in 0.103s — OK

./init.ps1
# [OK] Todos los bloques pasan (exit code 0)
```

## SOLID

- **S (Single Responsibility):** `src/config.py` solo modelo de dominio + persistencia. `src/main.py` solo endpoints HTTP.
- **O (Open/Closed):** Nuevos puertos se anaden agregando entradas a `VALID_TEST_PORTS` y casos en el endpoint test.
- **L (Liskov):** No hay herencia en este feature.
- **I (Interface Segregation):** Las dataclasses tienen solo los campos necesarios, sin metodos extra.
- **D (Dependency Inversion):** Los endpoints dependen de `SystemConfig` (abstraccion), no de YAML directamente.
