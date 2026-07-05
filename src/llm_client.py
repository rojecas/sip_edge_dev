"""Cliente HTTP para llama-server con soporte de Function Calling."""

import json
import logging
import time

import httpx

logger = logging.getLogger(__name__)


class LlamaConnectionError(Exception):
    """Se lanza cuando falla la comunicacion con llama-server."""


class LlamaClient:
    """Cliente HTTP para llama-server API /v1/chat/completions.

    Soporta Function Calling (tool_calls) via formato OpenAI API.
    En dev_mode, retorna respuestas simuladas sin conexion real.
    """

    def __init__(self, base_url: str, model: str, timeout: int, dev_mode: bool, api_key: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout
        self._dev_mode = dev_mode
        self._client: httpx.Client | None = None
        self._headers: dict[str, str] = {}

        if not dev_mode:
            self._client = httpx.Client(timeout=httpx.Timeout(timeout))
            if api_key:
                self._headers = {"Authorization": f"Bearer {api_key}"}
        logger.info(
            "LlamaClient inicializado: base_url=%s model=%s dev_mode=%s",
            base_url, model, dev_mode,
        )

    def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        """Envia un chat completion a llama-server.

        En dev mode, retorna respuesta simulada (predecible).
        En prod, hace POST a /v1/chat/completions.

        Retorna dict con formato OpenAI API: {'choices': [...], ...}

        Raises:
            LlamaConnectionError: si falla la conexion.
        """
        if self._dev_mode:
            return self._simulate_response(messages, tools)

        url = f"{self._base_url}/v1/chat/completions"
        payload = {
            "model": self._model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 512,
            "stream": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "required"

        try:
            response = self._client.post(url, json=payload, headers=self._headers)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.error("Timeout conectando a llama-server en %s", url)
            raise LlamaConnectionError(f"Timeout conectando a llama-server: {url}")
        except httpx.ConnectError:
            logger.error("Conexion rechazada por llama-server en %s", url)
            raise LlamaConnectionError(f"Conexion rechazada por llama-server: {url}")
        except httpx.HTTPStatusError as e:
            logger.error("llama-server respondio con error %d: %s", e.response.status_code, e)
            raise LlamaConnectionError(f"llama-server error {e.response.status_code}")
        except Exception as e:
            logger.error("Error inesperado en chat_completion: %s", e)
            raise LlamaConnectionError(f"Error inesperado: {e}")

    def close(self) -> None:
        """Cierra la sesion HTTP."""
        if self._client is not None:
            self._client.close()
            self._client = None
            logger.info("LlamaClient cerrado")

    # ------------------------------------------------------------------
    # Simulacion para dev_mode
    # ------------------------------------------------------------------

    def _simulate_response(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Genera una respuesta simulada para modo desarrollo.

        Si hay tools disponibles, simula un tool_call. Si no, genera texto.
        """
        user_text = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_text = str(msg.get("content", ""))
                break

        logger.info("[DEV_MODE] LlamaClient simulado — user query: %s", user_text[:100])

        # Si hay tools y no estamos en segunda vuelta, simular tool_call
        has_tool_results = any(
            msg.get("role") == "tool" for msg in messages
        )
        if tools and not has_tool_results:
            # Simular que el LLM decide llamar una tool
            tool_name = "get_basic_stats"
            if "hacienda" in user_text.lower():
                tool_name = "get_breakdown_by_hacienda"
            elif "operador" in user_text.lower() or "operator" in user_text.lower():
                tool_name = "get_breakdown_by_operator"
            elif "composicion" in user_text.lower() or "proporcion" in user_text.lower():
                tool_name = "get_material_composition"
            elif "turno" in user_text.lower():
                tool_name = "get_shift_summary"
            elif "anomal" in user_text.lower():
                tool_name = "detect_anomalies"
            elif "tendencia" in user_text.lower() or "trend" in user_text.lower():
                tool_name = "get_trend"

            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": f"call_{int(time.time()*1000)}",
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps({
                                    "fecha_inicio": "2026-01-01",
                                    "fecha_fin": "2026-12-31",
                                }),
                            },
                        }],
                    },
                }],
            }

        # Segunda vuelta o sin tools: generar respuesta de texto
        response_text = (
            f"[DEV_MODE] Respuesta simulada del LLM a: '{user_text[:80]}'. "
            "Los datos presentados son reales, obtenidos de la base de datos."
        )
        return {
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": response_text,
                },
            }],
        }


class DualBackendClient:
    """Cliente LLM con backend dual y circuit breaker con exponential backoff."""

    def __init__(self, primary, secondary, cooldown=30):
        self._primary = primary
        self._secondary = secondary
        self._state = "OK"
        self._cooldown = cooldown
        self._backoff = cooldown
        self._last_failure = 0.0

    def chat_completion(self, messages, tools=None):
        now = time.time()
        if self._state == "FALLBACK" and (now - self._last_failure) >= self._backoff:
            self._state = "PROBING"
            logger.info("DualBackend: probing primary after cooldown=%ds", self._backoff)

        if self._state in ("OK", "PROBING"):
            try:
                result = self._primary.chat_completion(messages, tools)
                self._on_success()
                return result
            except LlamaConnectionError as e:
                logger.warning("DualBackend: primary failed: %s", e)
                self._on_primary_failure()

        try:
            result = self._secondary.chat_completion(messages, tools)
            self._on_success()
            return result
        except LlamaConnectionError as e:
            logger.error("DualBackend: both backends failed")
            raise LlamaConnectionError("Both LLM backends unavailable") from e

    def _on_success(self):
        if self._state != "OK":
            logger.info("DualBackend: primary recovered, returning to OK")
        self._state = "OK"
        self._backoff = self._cooldown
        self._last_failure = 0.0

    def _on_primary_failure(self):
        self._last_failure = time.time()
        if self._state == "PROBING":
            self._backoff = min(self._backoff * 2, 300)
            logger.info("DualBackend: backoff doubled to %ds", self._backoff)
        self._state = "FALLBACK"

    def close(self):
        self._primary.close()
        self._secondary.close()
