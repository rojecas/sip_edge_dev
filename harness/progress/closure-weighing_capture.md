# Cierre — weighing_capture

- **Feature:** weighing_capture (id: 6)
- **Fecha:** 2026-06-14
- **Status final:** done

## Archivos

| Archivo | Accion |
|---------|--------|
| `src/models.py` | MODIFICADO — Weighing ORM model |
| `src/weighings.py` | CREADO — CRUD + WebSocket + RS232 stub |
| `src/auth.py` | MODIFICADO — require_any_role dependency |
| `src/main.py` | MODIFICADO — routers, WS /ws/scale, ScaleService callback |
| `src/haciendas.py` | MODIFICADO — GET endpoints accesibles por operator |
| `tests/test_weighings.py` | CREADO — 21 tests |
| `tests/test_haciendas.py` | MODIFICADO — operator GET tests |

## Verificacion

- `docker compose exec backend python -m unittest discover -s tests -v` → 195 tests OK
- `./init.ps1` → [OK]
- Reviewer: APPROVED
