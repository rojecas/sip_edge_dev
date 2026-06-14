# Cierre — system_config

- **Feature:** system_config (id: 1)
- **Fecha:** 2026-06-13
- **Status final:** done

## Archivos modificados

| Archivo | Accion |
|---------|--------|
| `src/config.py` | CREADO — Modelo de dominio + persistencia YAML |
| `src/main.py` | MODIFICADO — Endpoints GET/PUT/POST /api/config |
| `tests/test_config.py` | CREADO — 20 tests unitarios e integracion |
| `requirements.txt` | MODIFICADO — pyserial, httpx |
| `Dockerfile` | MODIFICADO — gh CLI, git, curl |

## Decisiones tecnicas

1. **Lifespan en lugar de on_event:** FastAPI 0.115.6 depreca `@app.on_event`, se uso `@asynccontextmanager` + `lifespan=`.
2. **pyserial condicional:** Import dentro de endpoints de test, no a nivel modulo.
3. **Atomicidad YAML:** `tempfile.mkstemp()` + `os.replace()`.
4. **GSM via ModemManager:** `subprocess.run(["mmcli", "-m", str(modem_index)])`, no AT commands.
5. **Defaults EdgeBox-RPI-200:** RS485=/dev/ttyACM0, RS232=/dev/ttyACM1, 115200 baud.

## Verificacion

- `docker compose exec backend python -m unittest discover -s tests -v` → 20 tests OK
- `./init.ps1` → [OK] todos los bloques
- Reviewer APPROVED → `harness/progress/review_system_config.md`
