# Plan de correccion: tool_choice=required impide parafraseo del LLM

## Sintoma
Cuando el sistema procesa una consulta SMS via IA (Feature 8 - ai_agent), el LLM
(DeepSeek) responde con `content: ""` en la segunda vuelta, lo que causa que
el usuario reciba "Sin respuesta." o "No se pudo generar una respuesta."

Esto ocurre porque:

1. **Primera vuelta (OK):** `tool_choice=required` fuerza al LLM a llamar tools SQL.
   DeepSeek responde con `tool_calls` correctos.
2. **Segunda vuelta (ROTA):** Tambien usa `tool_choice=required`, forzando al LLM
   a llamar tools OTRA VEZ en vez de generar texto parafraseando los resultados.
   DeepSeek devuelve `content: ""` + nuevos `tool_calls`.

## Causa raiz

### Problema A (CRITICO): `tool_choice=required` en segunda vuelta

**Archivo: `src/llm_client.py` linea 66-68**
```python
if tools:
    payload["tools"] = tools
    payload["tool_choice"] = "required"
```

`chat_completion()` NO acepta un parametro para controlar `tool_choice`.
Siempre usa `"required"` cuando hay tools. Esto es correcto para la primera
vuelta pero letal para la segunda.

**Archivo: `src/agent_orchestrator.py` linea 263**
```python
final_response = self._llm.chat_completion(messages, tools=TOOL_DEFINITIONS)
```
Pasa `tools=TOOL_DEFINITIONS` -> `tool_choice=required` -> LLM forzado a
llamar tools otra vez -> `content=""`.

**Archivo: `src/main.py` linea 515**
```python
response2 = llm_client.chat_completion(messages, tools=TOOL_DEFINITIONS)
```
Mismo problema en endpoint /api/agent/query.

### Problema B (MEDIO): System prompt sin ano actual

**Archivo: `src/agent_orchestrator.py` lineas 17-35**
El SYSTEM_PROMPT no incluye el ano actual. DeepSeek fue entrenado con data
hasta 2024 y asume ese ano por defecto.

### Problema C (BAJO): Simulacion en dev mode ignora tool_results

**Archivo: `src/llm_client.py` lineas 151-163**
`_simulate_response()` en segunda vuelta ignora completamente los tool_results
reales y solo responde con un placeholder.

## Archivos implicados

| Archivo | Cambio |
|---------|--------|
| `src/llm_client.py` | Anadir parametro `tool_choice` a `chat_completion()`, mejorar `_simulate_response` |
| `src/agent_orchestrator.py` | Segunda vuelta con `tools=None`, actualizar SYSTEM_PROMPT con ano |
| `src/main.py` | Segunda vuelta en endpoint /api/agent/query con `tools=None` |
| `tests/test_llm_client.py` | Tests para tool_choice parameter |
| `tests/test_agent_orchestrator.py` | Tests para segunda vuelta sin tools |

## Fix propuesto

### Fix A1: `src/llm_client.py`

Anadir parametro `tool_choice: str | None = None` a `chat_completion()`.
Cuando es `None` y hay tools, usa `"required"` (compatibilidad hacia atras).
Cuando tiene un valor explicito, usa ese valor.

Tambien actualizar `DualBackendClient.chat_completion()` para pasar `tool_choice`.

### Fix A2: `src/agent_orchestrator.py` linea 263

Cambiar `tools=TOOL_DEFINITIONS` a `tools=None` en la segunda vuelta.

### Fix A3: `src/main.py` linea 515

Cambiar `tools=TOOL_DEFINITIONS` a `tools=None` en la segunda vuelta.

### Fix B: `src/agent_orchestrator.py`

Anadir al SYSTEM_PROMPT: "El ano actual es 2026. Cuando el usuario no especifique
un ano, usa el ano actual 2026 como referencia."

### Fix C: `src/llm_client.py`

Mejorar `_simulate_response()` para que, cuando hay tool_results, genere un
resumen real con los datos obtenidos en vez de un placeholder generico.

## Plan de verificacion

1. `python -m unittest tests.test_llm_client -v` - Test de tool_choice parameter
2. `python -m unittest tests.test_agent_orchestrator -v` - Test de segunda vuelta sin tools
3. `python -m unittest discover -s tests -v` - Todos los tests pasan
4. `./harness/init.ps1` - Sin errores criticos
