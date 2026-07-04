# Closure — Bug 26 (emergency_request_wrong_sms)

## Sintoma
Al solicitar modo manual desde la vista Kiosko (POST /api/emergency/request), el administrador recibe en su telefono el mensaje "Lo siento, el sistema de analisis no esta disponible en este momento." en lugar del mensaje esperado de solicitud de emergencia.

## Causa raiz
La funcion `_build_ai_sms_handler()` en `src/main.py` construia un handler de SMS que SIEMPRE retornaba True, actuando como catch-all en el dispatcher v2. Cuando el sistema de emergencia enviaba un SMS al admin, el dispatcher lo procesaba y como el SMS no matcheaba "manual on" ni "reset password", caia al handler AI que retornaba True y ejecutaba `handle_sms_query()`. Al fallar la conexion al LLM (LlamaConnectionError), se enviaba el mensaje de error "Lo siento, el sistema de analisis no esta disponible en este momento."

## Archivos modificados
- `src/main.py`: Eliminado el registro del handler AI como handler del dispatcher v2 (bloque de 5 lineas). Eliminada la funcion `_build_ai_sms_handler()` (13 lineas).
- `tests/test_sms_dispatcher_v2.py`: Anadido test `test_no_catchall_handler_bug26_regression` que verifica que un SMS no reconocido recibe HELP_RESPONSE cuando los handlers solo responden a patrones especificos.

## Fix aplicado
1. Removidas las lineas 274-278 de `src/main.py`: el bloque `register_handler(_build_ai_sms_handler(...))`
2. Removidas las lineas 322-334 de `src/main.py`: la funcion `_build_ai_sms_handler()` completa
3. `AgentOrchestrator` y `app.state.agent_orchestrator` se mantienen porque otras partes del sistema (endpoint `/agent/query`, reportes programados, deteccion de anomalias) los usan

## Regression test
Archivo: `tests/test_sms_dispatcher_v2.py` — metodo `test_no_catchall_handler_bug26_regression`
Escenario:
1. Se registran dos handlers que solo retornan True para textos especificos ("manual on", "reset password")
2. Se envia SMS "hola" (no reconocido)
3. Ningun handler retorna True → dispatcher responde con HELP_RESPONSE

## Resultado de verificacion
- `./init.ps1`: no aplica (el proyecto corre en Docker, los tests se ejecutaron via `docker compose exec backend python -m unittest discover -s tests -p "test_sms*.py"`)
- Todos los 73 tests SMS pasaron OK
- Servicio reiniciado en EdgeBox: `systemctl restart sip-edge` OK
- Health check: `{"status":"healthy"}` retorna 200
- Endpoint `/agent/query` no afectado (sigue usando `app.state.agent_orchestrator` directamente)

## Notas
- Bug reportado originalmente como Bug 26. El fix es minimalista: solo elimina el handler catch-all AI del dispatcher v2.
- La Feature 27 (sms_persistence) prometia eliminar el catch-all (R5). Este fix completa esa promesa.
