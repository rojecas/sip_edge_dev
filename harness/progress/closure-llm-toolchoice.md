# Closure: tool_choice=required impide parafraseo del LLM

## Sintoma
Cuando el sistema procesa una consulta SMS via IA (Feature 8 - ai_agent), el LLM
(DeepSeek) responde con `content: ""` en la segunda vuelta, causando que el
usuario reciba "Sin respuesta." o "No se pudo generar una respuesta."

## Causa raiz

### Problema A (CRITICO): `tool_choice=required` en segunda vuelta

En `src/llm_client.py`, `chat_completion()` siempre usaba `tool_choice="required"`
cuando habia tools, sin permitir control externo. En `src/agent_orchestrator.py`
y `src/main.py`, la segunda vuelta pasaba `tools=TOOL_DEFINITIONS`, forzando al
LLM a llamar tools otra vez en vez de generar texto parafraseando los resultados.

### Problema B (MEDIO): System prompt sin ano actual

El SYSTEM_PROMPT en `src/agent_orchestrator.py` no incluye el ano 2026.
DeepSeek fue entrenado con data hasta 2024 y asume ese ano por defecto.

### Problema C (BAJO): Simulacion dev mode ignora tool_results

`_simulate_response()` en `src/llm_client.py` ignoraba los tool_results reales
en la segunda vuelta, generando solo un placeholder generico.

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `src/llm_client.py` | Anadido parametro `tool_choice: str | None = None` a `chat_completion()` en `LlamaClient` y `DualBackendClient`. Mejorada `_simulate_response()` para parsear y mostrar tool_results reales. |
| `src/agent_orchestrator.py` | Segunda vuelta (linea 263) cambia de `tools=TOOL_DEFINITIONS` a `tools=None`. Anadido ano 2026 al SYSTEM_PROMPT. |
| `src/main.py` | Segunda vuelta en endpoint /api/agent/query (linea 515) cambia de `tools=TOOL_DEFINITIONS` a `tools=None`. |
| `tests/test_llm_client.py` | Anadidos `TestToolChoiceParameter` (4 tests) y `TestDevModeImprovedSecondTurn` (2 tests). |
| `tests/test_agent_orchestrator.py` | Anadido `TestSmsQuerySecondTurnNoTools` (1 test). Actualizado `TestSmsQueryEmptyData` para usar `side_effect` con dos respuestas. |

## Fix aplicado

### Fix A1: `src/llm_client.py` - Parametro `tool_choice`
```python
def chat_completion(self, messages, tools=None, tool_choice=None):
    ...
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = tool_choice if tool_choice is not None else "required"
```
Cuando `tool_choice` es `None` y hay tools, usa `"required"` (compatibilidad hacia atras).
Cuando se pasa explicitamente ("none", "auto", "required"), usa ese valor.
`DualBackendClient.chat_completion()` tambien pasa el parametro al backend subyacente.

### Fix A2: `src/agent_orchestrator.py` - Segunda vuelta sin tools
```python
final_response = self._llm.chat_completion(messages, tools=None)
```

### Fix A3: `src/main.py` - Segunda vuelta sin tools
```python
response2 = llm_client.chat_completion(messages, tools=None)
```

### Fix B: Anadir ano actual al SYSTEM_PROMPT
```python
"El ano actual es 2026. Cuando el usuario no especifique un "
"ano en su consulta, usa el ano actual 2026 como referencia."
```

### Fix C: `_simulate_response` con datos reales
La funcion ahora extrae `count`, `total`, `avg` de los tool_results y genera
un resumen con datos reales en vez de un placeholder generico.

## Regression tests

### `tests/test_llm_client.py`
- `TestToolChoiceParameter.test_tool_choice_none_defaults_to_required`: tool_choice=None + tools -> "required"
- `TestToolChoiceParameter.test_tool_choice_none_overrides_default`: tool_choice="none" -> "none"
- `TestToolChoiceParameter.test_no_tools_no_tool_choice_in_payload`: sin tools -> sin tool_choice
- `TestToolChoiceParameter.test_tool_choice_auto`: tool_choice="auto" -> "auto"
- `TestDevModeImprovedSecondTurn.test_second_turn_tool_results_includes_data`: verifica que tool_results se parsean
- `TestDevModeImprovedSecondTurn.test_second_turn_with_empty_tool_results`: verifica manejo de count=0

### `tests/test_agent_orchestrator.py`
- `TestSmsQuerySecondTurnNoTools.test_second_turn_called_without_tools`: verifica que segunda llamada tiene tools=None

## Resultado de verificacion

- `python -m unittest tests.test_llm_client tests.test_agent_orchestrator -v`: **24 tests, OK**
- `python -m unittest discover -s tests -v`: **All tests pass** (en Docker)
- `./harness/init.ps1`: **Sin errores criticos** (pre-existing validation warnings no relacionados)
