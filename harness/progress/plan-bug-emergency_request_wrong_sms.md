# Plan Bug 26 — emergency_request_wrong_sms

## Sintoma
Al solicitar modo manual desde la vista Kiosko (POST /api/emergency/request), el administrador recibe en su telefono el mensaje "Lo siento, el sistema de analisis no esta disponible en este momento." en lugar del mensaje esperado de solicitud de emergencia.

## Causa raiz
El dispatcher v2 (`sms_dispatcher_v2.py`) esta diseñado correctamente: procesa handlers en orden (emergency → password_reset → ai_query), y si NINGUN handler retorna True, responde con HELP_RESPONSE "Comando no reconocido...".

Sin embargo, la funcion `_build_ai_sms_handler()` en `src/main.py` (lineas 322-334) construye un handler que **SIEMPRE retorna True**, actuando como catch-all:

```python
def handler(sender_phone: str, text: str) -> bool:
    agent_orchestrator.handle_sms_query(sender_phone, text)
    return True  # Siempre procesa como fallback
```

Cuando se solicita emergencia desde el kiosko (no via SMS), el sistema envia un SMS al admin con la solicitud. El SMS es recibido por el modem, el dispatcher lo procesa y como no matchea emergency (no dice "manual on") ni password_reset, cae al handler AI que retorna True y ejecuta `handle_sms_query()`, que al no poder conectar con el LLM, envia el mensaje de error "Lo siento, el sistema de analisis no esta disponible en este momento."

## Archivos implicados
- `src/main.py` — Eliminar registro del handler AI en el dispatcher v2 (lineas 274-278) y eliminar la funcion `_build_ai_sms_handler()` (lineas 322-334)

## Fix propuesto
1. En `src/main.py`: Eliminar las lineas que registran el handler AI como handler del dispatcher v2 (lineas 274-278)
2. Eliminar la funcion `_build_ai_sms_handler()` (lineas 322-334)
3. Mantener `AgentOrchestrator` y `app.state.agent_orchestrator` porque otras partes del sistema (endpoint `/agent/query`, reportes programados, deteccion de anomalias) lo usan

Con este cambio:
- SMS "hola" u otros no reconocidos → ningun handler retorna True → dispatcher envia HELP_RESPONSE ("Comando no reconocido...")
- SMS "manual on" → handler emergency lo procesa
- SMS "reset password <user>" → handler password_reset lo procesa
- La solicitud de emergencia desde kiosko envia SMS directo, sin pasar por el dispatcher

## Plan de verificacion
1. Aplicar cambios en `src/main.py`
2. Reiniciar servicio: `echo sipedge1234 | sudo -S systemctl restart sip-edge`
3. Verificar health check: `curl -s http://127.0.0.1:8000/health`
4. Verificar logs: `sudo journalctl -u sip-edge --no-pager -n 30` — sin errores
5. Verificar que el endpoint `/agent/query` sigue funcionando (usa `app.state.agent_orchestrator` directamente)
