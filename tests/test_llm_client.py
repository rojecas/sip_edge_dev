"""Tests for LlamaClient: dev mode, prod mode, connection errors."""

import json
import unittest
from unittest import mock

import httpx

from src.llm_client import LlamaClient, LlamaConnectionError


class TestLlamaClientDevMode(unittest.TestCase):
    """T30: Verificar que en dev mode no hace HTTP."""

    def setUp(self):
        self.client = LlamaClient(
            base_url="http://localhost:8080",
            model="test-model",
            timeout=10,
            dev_mode=True,
        )

    def tearDown(self):
        self.client.close()

    def test_dev_mode_returns_simulated_response(self):
        """R22: En dev mode, retorna respuesta simulada sin HTTP."""
        with self.assertLogs("src.llm_client", level="INFO") as log_ctx:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": "Cuantos pesajes hoy?"}],
            )
        self.assertIn("choices", response)
        choices = response["choices"]
        self.assertGreater(len(choices), 0)
        content = choices[0]["message"]["content"]
        self.assertIn("[DEV_MODE]", content)
        self.assertTrue(
            any("[DEV_MODE] LlamaClient simulado" in msg for msg in log_ctx.output)
        )

    def test_dev_mode_simulates_tool_call(self):
        """R22: En dev mode, con tools disponibles, simula tool_call."""
        tools = [{"type": "function", "function": {"name": "get_basic_stats", "description": "..."}}]
        response = self.client.chat_completion(
            messages=[{"role": "user", "content": "Estadisticas de hoy"}],
            tools=tools,
        )
        choices = response["choices"]
        msg = choices[0]["message"]
        self.assertIn("tool_calls", msg)

    def test_dev_mode_simulates_second_turn(self):
        """R22: En dev mode, si ya hay tool results, genera texto."""
        tools = [{"type": "function", "function": {"name": "get_basic_stats", "description": "..."}}]
        response = self.client.chat_completion(
            messages=[
                {"role": "user", "content": "Estadisticas de hoy"},
                {"role": "tool", "tool_call_id": "call_1", "content": '{"count": 5}'},
            ],
            tools=tools,
        )
        choices = response["choices"]
        content = choices[0]["message"]["content"]
        self.assertIn("[DEV_MODE]", content)


class TestLlamaClientProdMode(unittest.TestCase):
    """T30: Verificar POST a la URL correcta."""

    def setUp(self):
        self.client = LlamaClient(
            base_url="http://localhost:8080",
            model="test-model",
            timeout=10,
            dev_mode=False,
        )

    def tearDown(self):
        self.client.close()

    @mock.patch.object(httpx.Client, "post")
    def test_chat_completion_posts_to_correct_url(self, mock_post):
        """R14: Debe hacer POST a /v1/chat/completions."""
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Respuesta"}}],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        self.client.chat_completion(
            messages=[{"role": "user", "content": "Hola"}],
        )

        mock_post.assert_called_once()
        call_args = mock_post.call_args[0]
        self.assertIn("/v1/chat/completions", call_args[0])

    @mock.patch.object(httpx.Client, "post")
    def test_chat_completion_includes_tools(self, mock_post):
        """R14: Si hay tools, se incluyen en el payload."""
        mock_response = mock.MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"role": "assistant", "content": "Ok"}}],
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        tools = [{"type": "function", "function": {"name": "get_basic_stats"}}]
        self.client.chat_completion(
            messages=[{"role": "user", "content": "Stats"}],
            tools=tools,
        )

        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        self.assertIn("tools", payload)


class TestLlamaClientConnectionError(unittest.TestCase):
    """T30: Verificar LlamaConnectionError al fallar conexion."""

    def setUp(self):
        self.client = LlamaClient(
            base_url="http://localhost:9999",
            model="test-model",
            timeout=1,
            dev_mode=False,
        )

    def tearDown(self):
        self.client.close()

    @mock.patch.object(httpx.Client, "post")
    def test_timeout_raises_llama_connection_error(self, mock_post):
        """R21: Timeout debe lanzar LlamaConnectionError."""
        mock_post.side_effect = httpx.TimeoutException("timeout")

        with self.assertRaises(LlamaConnectionError):
            self.client.chat_completion(
                messages=[{"role": "user", "content": "Hola"}],
            )

    @mock.patch.object(httpx.Client, "post")
    def test_connect_error_raises_llama_connection_error(self, mock_post):
        """R21: Conexion rechazada debe lanzar LlamaConnectionError."""
        mock_post.side_effect = httpx.ConnectError("connection refused")

        with self.assertRaises(LlamaConnectionError):
            self.client.chat_completion(
                messages=[{"role": "user", "content": "Hola"}],
            )

    @mock.patch.object(httpx.Client, "post")
    def test_http_error_raises_llama_connection_error(self, mock_post):
        """R21: Error HTTP 5xx debe lanzar LlamaConnectionError."""
        mock_response = mock.MagicMock()
        mock_response.status_code = 500
        mock_post.side_effect = httpx.HTTPStatusError(
            "server error", request=mock.MagicMock(), response=mock_response
        )

        with self.assertRaises(LlamaConnectionError):
            self.client.chat_completion(
                messages=[{"role": "user", "content": "Hola"}],
            )


class TestLlamaClientClose(unittest.TestCase):
    """T30: Verificar que close no falla."""

    def test_close_without_client(self):
        client = LlamaClient(
            base_url="http://localhost:8080",
            model="test",
            timeout=10,
            dev_mode=True,
        )
        client.close()  # No debe fallar

    def test_close_prod_client(self):
        client = LlamaClient(
            base_url="http://localhost:8080",
            model="test",
            timeout=10,
            dev_mode=False,
        )
        client.close()  # No debe fallar
