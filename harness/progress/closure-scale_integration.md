# Closure — scale_integration

**Feature:** 05_scale_integration — Integracion Serial con Bascula DINI ARGEO DFWLI-2  
**Date:** 2026-06-13  
**Agent:** implementer  
**Status:** done

## Files created
- `src/scale.py` — ScaleService singleton, parseo de respuestas extendida/corta, excepciones (ScaleConnectionError, ScaleTimeoutError, ScaleProtocolError)
- `tests/test_scale.py` — 30 tests cubriendo todas las R

## Files modified
- `src/config.py`: Anadido `ScaleConfig` dataclass, `DEFAULT_SCALE_TIMEOUT = 3`, `load_config` retorna tupla de 3, `save_scale_config`, actualizado `_atomic_write_sections` y `_save_system_config_atomic`
- `src/main.py`: ScaleService inicializado en lifespan (start/stop), endpoint `PUT /api/setup/scale` con `ScaleTimeoutRequest`
- `tests/test_config.py`: Callers de `load_config` actualizados a 3-tuple
- `tests/test_users.py`: `ScaleConfig` anadido a app state en setup

## Technical decisions
- Threading + queue for async serial reading (not asyncio — pyserial is blocking)
- Threading.Lock for write serialization
- Atomic write pattern for config.yaml persistence (scale section)
- Pydantic Field(ge=1, le=10) for timeout validation on the endpoint
- Mock serial.Serial for unit tests (no hardware dependency in CI)

## Verification
- `python -m unittest discover -s tests`: 174 tests, all OK
- `./init.ps1`: All blocks [OK]
