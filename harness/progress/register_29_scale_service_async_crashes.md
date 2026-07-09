# Registro — Release Manager: Bug #29

## Fecha: 2026-07-09

## Item registrado

| Campo | Valor |
|-------|-------|
| **ID** | 29 |
| **Tipo** | bug |
| **Nombre** | `scale_service_async_crashes` |
| **Titulo** | ScaleService async reader crashes + WebSocket send_text nunca se ejecuta |
| **Closure** | `harness/progress/closure-scale_service_async_crashes.md` |

## Acciones realizadas

### 1. Agregar entrada en `tracker.json` → `pending`
✅ Entrada agregada a `harness/releases/tracker.json` en el arreglo `pending`.

### 2. Cerrar GitHub issue (#23)
❌ Fallo — `github_sync.py` arrojo `UnicodeDecodeError` al leer `feature_list.json` (el archivo contiene caracteres UTF-8 que no pueden decodificarse como cp1252). Este error no bloquea el registro segun las reglas del release-manager.

### 3. Marcar `done` en `feature_list.json`
✅ Ya estaba marcado como `done` (no requiere modificacion).

## Resumen del closure

Tres bugs en ScaleService corregidos:
- **Bug 1:** `_async_reader` se rompia con TypeError/SerialException sin recuperacion → `_recover_serial()` con backoff
- **Bug 2a:** Queue solo se drenaba al salir del while → `_process_async_queue()` dentro del loop
- **Bug 2b:** `ws.send_text()` nunca ejecutado desde thread background → `_event_loop` module-level
- **Bug 3:** `logging.basicConfig()` despues de `ScaleService.start()` → movido antes

46 regression tests OK (33 test_scale + 13 test_main).
