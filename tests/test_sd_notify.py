"""Tests for the sd_notify module (systemd watchdog notifications)."""
import os
import socket
import tempfile
import unittest
from unittest.mock import patch


class TestSdNotify(unittest.TestCase):
    """Test suite for src.sd_notify."""

    def setUp(self):
        self._env_backup = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env_backup)

    def test_notify_sends_datagram(self):
        """Verifica que notify() envia WATCHDOG=1\\n a un socket Unix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sock_path = os.path.join(tmpdir, "notify.sock")
            # Create a datagram Unix socket to receive the notification
            server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            server.bind(sock_path)
            server.settimeout(1.0)

            os.environ["NOTIFY_SOCKET"] = sock_path

            from src.sd_notify import notify
            result = notify()

            self.assertTrue(result)
            data, _ = server.recvfrom(1024)
            self.assertEqual(data, b"WATCHDOG=1\n")
            server.close()

    def test_notify_no_socket_variable(self):
        """Verifica que notify() no falle si NOTIFY_SOCKET no esta definido."""
        os.environ.pop("NOTIFY_SOCKET", None)

        from src.sd_notify import notify
        result = notify()

        self.assertFalse(result)

    def test_notify_empty_socket_variable(self):
        """Verifica que notify() no falle si NOTIFY_SOCKET esta vacio."""
        os.environ["NOTIFY_SOCKET"] = ""

        from src.sd_notify import notify
        result = notify()

        self.assertFalse(result)

    def test_notify_bad_socket_path(self):
        """Verifica que notify() no lance excepcion con socket inexistente."""
        os.environ["NOTIFY_SOCKET"] = "/tmp/nonexistent/socket"

        from src.sd_notify import notify
        result = notify()

        self.assertFalse(result)

    def test_notify_abstract_socket(self):
        """Verifica que notify() maneje sockets abstractos (@ syntax)."""
        # Abstract sockets are Linux-specific; we test the "@" -> "\0" translation
        # by creating a regular socket but setting NOTIFY_SOCKET with "@"
        with tempfile.TemporaryDirectory() as tmpdir:
            sock_path = os.path.join(tmpdir, "abstract_test.sock")
            server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            server.bind(sock_path)
            server.settimeout(1.0)

            # Set NOTIFY_SOCKET with "@" prefix pointing to the real path
            os.environ["NOTIFY_SOCKET"] = "@" + sock_path

            from src.sd_notify import notify
            result = notify()

            # The "@" prefix will be converted to "\0" + path, which won't match
            # a real filesystem socket, so this should return False gracefully
            self.assertFalse(result)
            server.close()

    def test_notify_logs_error_on_failure(self):
        """Verifica que notify() registre un debug log en caso de error."""
        os.environ["NOTIFY_SOCKET"] = "/tmp/nonexistent/socket"

        from src.sd_notify import notify
        with self.assertLogs("src.sd_notify", level="DEBUG") as logs:
            result = notify()

        self.assertFalse(result)
        self.assertTrue(any("sd_notify failed" in msg for msg in logs.output))

    def test_main_imports_sd_notify(self):
        """Verifica que main.py pueda importar sd_notify correctamente."""
        from src.sd_notify import notify
        self.assertIsNotNone(notify)
