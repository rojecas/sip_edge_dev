"""Tests for POST /api/scale/command endpoint (T37)."""

import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.scale import ScaleConnectionError, ScaleProtocolError, ScaleTimeoutError


class TestScaleCommandEndpoint(unittest.TestCase):
    """Tests for POST /api/scale/command (T37)."""

    @classmethod
    def setUpClass(cls):
        from src.main import app
        from src.config import SessionConfig
        from src.auth import get_current_user

        # Override auth dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 1, "role": "operator", "iat": 9999999999,
        }

        # Set up session config
        app.state.session = SessionConfig(session_timeout_minutes=999999)

        # Create mock ScaleService
        cls.mock_scale = MagicMock()
        app.state.scale_service = cls.mock_scale

        cls.client = TestClient(app, raise_server_exceptions=False)

    def setUp(self):
        """Reset mock before each test."""
        self.mock_scale.reset_mock()
        # Explicitly reset send_command to a clean state
        self.mock_scale.send_command = MagicMock()

    def test_rext_command_returns_weight(self):
        """Send READ and receive net_weight in response."""
        self.mock_scale.send_command.return_value = {
            "net_weight": 150.500, "is_stable": True, "unit": "kg",
        }
        response = self.client.post("/api/scale/command", json={"command": "READ"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["net_weight"], 150.500)
        self.assertTrue(data["is_stable"])
        self.assertEqual(data["unit"], "kg")
        self.mock_scale.send_command.assert_called_once_with("READ", None)

    def test_tare_command_returns_ok(self):
        """Send TARE and receive result: ok."""
        self.mock_scale.send_command.return_value = {"result": "ok"}
        response = self.client.post("/api/scale/command", json={"command": "TARE"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["result"], "ok")
        self.mock_scale.send_command.assert_called_once_with("TARE", None)

    def test_unknown_command_returns_400(self):
        """Unknown command raises ScaleProtocolError -> HTTP 400."""
        self.mock_scale.send_command.side_effect = ScaleProtocolError(
            "Unknown command: BADCMD"
        )
        response = self.client.post("/api/scale/command", json={"command": "BADCMD"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("BADCMD", response.json()["detail"])

    def test_scale_disconnected_returns_503(self):
        """ScaleConnectionError returns HTTP 503."""
        self.mock_scale.send_command.side_effect = ScaleConnectionError(
            "Serial port not open"
        )
        response = self.client.post("/api/scale/command", json={"command": "READ"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("Serial port not open", response.json()["detail"])

    def test_scale_timeout_returns_503(self):
        """ScaleTimeoutError returns HTTP 503."""
        self.mock_scale.send_command.side_effect = ScaleTimeoutError(
            "No response within 3s"
        )
        response = self.client.post("/api/scale/command", json={"command": "READ"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("No response", response.json()["detail"])
