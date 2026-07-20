# Sesión F36 — 2026-07-20

## Feature: 36 — hacienda_search_filter
## Estado final: done

## Ciclo completo
1. spec-author → spec_ready (11 requisitos EARS)
2. spec-reviewed → aprobado por humano
3. implementer → 18/18 tareas completas
4. reviewer → CHANGES_REQUESTED (AdminSuertes código muerto + 13 tests legacy)
5. implementer (fix) → corregido, reviewer APPROVED
6. testing → 3 bugs encontrados y corregidos
7. release-manager → done, Issue #24 cerrado

## Bugs corregidos en testing
1. **Filtro ignorado** — uvicorn no recargó cambios de `src/haciendas.py`. `docker compose restart backend` solucionó.
2. **Acentos (`\u00f3` literal)** — Svelte no interpreta `\u` escapes en templates HTML. Reemplazados por UTF-8 real en 3 archivos.
3. **Timeout (regresión bug #40)** — Middleware excluye polling paths. InactivityGuard sin DOM listeners. Añadidos listeners + refreshToken periódico.

## Archivos modificados (adicionales a la implementación original)
- `src/haciendas.py`: parámetro `search` + filtro `func.lower()` (restaurado tras git checkout accidental)
- `frontend/src/components/InactivityGuard.svelte`: DOM listeners (mousedown, keydown, touchstart, mousemove) + refreshToken
- `frontend/src/components/HaciendaCodeInput.svelte`: `\u` escapes → UTF-8 real en templates
- `frontend/src/components/KioskForm.svelte`: `\u` escapes → UTF-8 real
- `frontend/src/components/AdminSuertes.svelte`: `\u` escapes → UTF-8 real
- `src/static/`: bundle recompilado (index-bGdsX-7V.js)

## init.ps1
- Backend: 715 tests, 7 fallos (todos pre-existentes: 1 orden de tests auth, 6 protocolo DFW06L)
- F36 tests: 20/20 OK (4 backend search + 13 AdminSuertes + 7 HaciendaCodeInput)
- Frontend build: exitoso

## Próxima sesión
- Features pendientes: 32 (sample_imaging), 33 (sql_tools_v2), 34 (alert_monitor), 35 (sms_scheduling_v2), 37 (notas_muestras)
