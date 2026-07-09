"""Tests for scale integration module."""

import os
import serial
import tempfile
import time
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from src.config import (
    BackupConfig,
    DEFAULT_SCALE_TIMEOUT,
    DEFAULT_SESSION_TIMEOUT_MINUTES,
    ScaleConfig,
    SessionConfig,
    default_config,
    load_config,
    save_scale_config,
)
from src.scale import (
    ScaleConnectionError,
    ScaleProtocolError,
    ScaleService,
    ScaleTimeoutError,
    parse_extended_response,
    parse_short_response,
)


class TestParseExtendedResponse(unittest.TestCase):
    def test_parse_extended_stable(self):
        line = "01ST,1, 0.0,PT 20.8, 0,kg\r\n"
        result = parse_extended_response(line)
        self.assertEqual(result["address"], "01")
        self.assertEqual(result["status_code"], "ST")
        self.assertTrue(result["is_stable"])
        self.assertEqual(result["net_weight"], 0.0)
        self.assertEqual(result["tare_indicator"], "PT")
        self.assertEqual(result["tare_weight"], 20.8)
        self.assertEqual(result["piece_count"], 0)
        self.assertEqual(result["unit"], "kg")

    def test_parse_extended_unstable(self):
        line = "01US,1, 5.2,PT 1.0, 3,kg\r\n"
        result = parse_extended_response(line)
        self.assertEqual(result["address"], "01")
        self.assertEqual(result["status_code"], "US")
        self.assertFalse(result["is_stable"])
        self.assertEqual(result["net_weight"], 5.2)
        self.assertEqual(result["piece_count"], 3)

    def test_parse_extended_overload(self):
        line = "01OL,1, 99999.9,  , 0,kg\r\n"
        result = parse_extended_response(line)
        self.assertEqual(result["status_code"], "OL")
        self.assertFalse(result["is_stable"])

    def test_parse_short_response(self):
        line = "01US,GS, 5.2,kg\r\n"
        result = parse_short_response(line)
        self.assertEqual(result["address"], "01")
        self.assertEqual(result["status_code"], "US")
        self.assertFalse(result["is_stable"])
        self.assertEqual(result["weight"], 5.2)
        self.assertEqual(result["unit"], "kg")

    def test_parse_short_stable(self):
        line = "01ST,GS, 0.0,kg\r\n"
        result = parse_short_response(line)
        self.assertTrue(result["is_stable"])
        self.assertEqual(result["weight"], 0.0)

    def test_parse_invalid_response(self):
        with self.assertRaises(ScaleProtocolError):
            parse_extended_response("garbage")
        with self.assertRaises(ScaleProtocolError):
            parse_short_response("garbage")

    def test_parse_extended_wrong_field_count(self):
        with self.assertRaises(ScaleProtocolError):
            parse_extended_response("01ST,1, 0.0,kg\r\n")


class TestScaleConfig(unittest.TestCase):
    def test_scale_config_default(self):
        config = ScaleConfig(timeout_seconds=DEFAULT_SCALE_TIMEOUT)
        self.assertEqual(config.timeout_seconds, 3)

    def test_scale_config_immutable(self):
        config = ScaleConfig(timeout_seconds=5)
        with self.assertRaises(Exception):
            config.timeout_seconds = 10

    def test_save_scale_config_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "config.yaml")
            cfg, sess, scale, backup, sms, _ = load_config(path)
            self.assertEqual(scale.timeout_seconds, DEFAULT_SCALE_TIMEOUT)
            new_scale = ScaleConfig(timeout_seconds=7)
            save_scale_config(new_scale, path)
            _, _, reloaded, _, _, _ = load_config(path)
            self.assertEqual(reloaded.timeout_seconds, 7)

    def test_load_scale_config_invalid_timeout_falls_back(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "config.yaml")
            import yaml
            os.makedirs(os.path.dirname(path), exist_ok=True)
            data = {
                "rs485": {"path": "/dev/ttyACM0", "baudrate": 115200, "parity": "N", "data_bits": 8, "stop_bits": 1.0},
                "rs232": {"path": "/dev/ttyACM1", "baudrate": 115200, "parity": "N", "data_bits": 8, "stop_bits": 1.0},
                "gsm": {"modem_index": 0},
                "last_updated": "2026-01-01T00:00:00",
                "session": {"session_timeout_minutes": 15},
                "scale": {"timeout_seconds": 99},
            }
            with open(path, "w") as f:
                yaml.dump(data, f)
            _, _, scale, _, _, _ = load_config(path)
            self.assertEqual(scale.timeout_seconds, DEFAULT_SCALE_TIMEOUT)


class TestScaleServiceCommands(unittest.TestCase):
    def setUp(self):
        self.config = ScaleConfig(timeout_seconds=3)
        self.serial_config = mock.MagicMock()
        self.serial_config.path = "/dev/ttyACM0"
        self.serial_config.baudrate = 115200
        self.serial_config.parity = "N"
        self.serial_config.data_bits = 8
        self.serial_config.stop_bits = 1.0

    @mock.patch("src.scale.serial.Serial")
    def test_send_rext(self, mock_serial):
        instance = mock_serial.return_value
        instance.readline.return_value = b"00ST,1, 10.5,PT 2.0, 0,kg\r\n"
        service = ScaleService(self.config, self.serial_config)
        service.start()
        result = service.send_command("REXT")
        self.assertEqual(result["net_weight"], 10.5)
        self.assertTrue(result["is_stable"])
        instance.write.assert_called_once_with(b"00REXT\r\n")
        service.stop()

    @mock.patch("src.scale.serial.Serial")
    def test_send_tare(self, mock_serial):
        instance = mock_serial.return_value
        instance.readline.return_value = b"OK\r\n"
        service = ScaleService(self.config, self.serial_config)
        service.start()
        result = service.send_command("TARE")
        self.assertEqual(result, {"result": "ok"})
        instance.write.assert_called_once_with(b"00TARE\r\n")
        service.stop()

    @mock.patch("src.scale.serial.Serial")
    def test_send_tman(self, mock_serial):
        instance = mock_serial.return_value
        instance.readline.return_value = b"OK\r\n"
        service = ScaleService(self.config, self.serial_config)
        service.start()
        result = service.send_command("TMAN", value="1.56")
        self.assertEqual(result, {"result": "ok"})
        instance.write.assert_called_once_with(b"00TMAN1.56\r\n")
        service.stop()

    @mock.patch("src.scale.serial.Serial")
    def test_send_zero(self, mock_serial):
        instance = mock_serial.return_value
        instance.readline.return_value = b"OK\r\n"
        service = ScaleService(self.config, self.serial_config)
        service.start()
        result = service.send_command("ZERO")
        self.assertEqual(result, {"result": "ok"})
        instance.write.assert_called_once_with(b"00ZERO\r\n")
        service.stop()

    @mock.patch("src.scale.serial.Serial")
    def test_send_clear(self, mock_serial):
        instance = mock_serial.return_value
        instance.readline.return_value = b"OK\r\n"
        service = ScaleService(self.config, self.serial_config)
        service.start()
        result = service.send_command("CLEAR")
        self.assertEqual(result, {"result": "ok"})
        instance.write.assert_called_once_with(b"00CLEAR\r\n")
        service.stop()

    @mock.patch("src.scale.serial.Serial")
    def test_send_command_timeout(self, mock_serial):
        instance = mock_serial.return_value
        instance.readline.side_effect = serial.SerialTimeoutException("timeout")
        service = ScaleService(self.config, self.serial_config)
        service.start()
        with self.assertRaises(ScaleTimeoutError):
            service.send_command("REXT")
        service.stop()

    @mock.patch("src.scale.serial.Serial")
    def test_send_command_empty_response_timeout(self, mock_serial):
        instance = mock_serial.return_value
        instance.readline.return_value = b""
        service = ScaleService(self.config, self.serial_config)
        service.start()
        with self.assertRaises(ScaleTimeoutError):
            service.send_command("REXT")
        service.stop()

    @mock.patch("src.scale.serial.Serial")
    def test_send_command_unknown_command(self, mock_serial):
        service = ScaleService(self.config, self.serial_config)
        service.start()
        with self.assertRaises(ScaleProtocolError):
            service.send_command("INVALID")
        service.stop()

    @mock.patch("src.scale.serial.Serial")
    def test_send_tman_without_value(self, mock_serial):
        service = ScaleService(self.config, self.serial_config)
        service.start()
        with self.assertRaises(ScaleProtocolError):
            service.send_command("TMAN")
        service.stop()

    @mock.patch("src.scale.serial.Serial")
    def test_start_connection_error(self, mock_serial):
        mock_serial.side_effect = OSError("Port not found")
        with self.assertRaises(ScaleConnectionError):
            service = ScaleService(self.config, self.serial_config)
            service.start()

    @mock.patch("src.scale.serial.Serial")
    def test_send_command_not_started(self, mock_serial):
        service = ScaleService(self.config, self.serial_config)
        with self.assertRaises(ScaleConnectionError):
            service.send_command("REXT")

    @mock.patch("src.scale.serial.Serial")
    def test_update_timeout(self, mock_serial):
        instance = mock_serial.return_value
        instance.readline.return_value = b"00ST,1, 0.0,PT 0.0, 0,kg\r\n"
        service = ScaleService(self.config, self.serial_config)
        service.update_timeout(10)
        service.start()
        result = service.send_command("REXT")
        self.assertTrue(result["is_stable"])
        service.stop()


class TestScaleAsyncListener(unittest.TestCase):
    @mock.patch("src.scale.serial.Serial")
    def test_async_listener_receives_data(self, mock_serial):
        config = ScaleConfig(timeout_seconds=3)
        serial_config = mock.MagicMock()
        serial_config.path = "/dev/ttyACM0"
        serial_config.baudrate = 115200
        serial_config.parity = "N"
        serial_config.data_bits = 8
        serial_config.stop_bits = 1.0
        received = []

        def callback(data):
            received.append(data)

        instance = mock_serial.return_value
        instance.readline.side_effect = [
            b"01ST,1, 10.0,PT 0.0, 0,kg\r\n",
            b"",
            StopIteration,
        ]
        service = ScaleService(config, serial_config)
        service.async_listener(callback)
        service.start()
        time.sleep(0.3)
        service.stop()
        self.assertGreaterEqual(len(received), 1)
        if received:
            self.assertEqual(received[0]["net_weight"], 10.0)


class TestScaleEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from src.main import app
        from src.auth import get_current_user
        import src.main as main_mod

        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.original_config_path = main_mod.CONFIG_PATH
        cls.config_path = os.path.join(cls.temp_dir.name, "config.yaml")
        main_mod.CONFIG_PATH = cls.config_path
        cfg, sess, scale, backup, sms, _ = load_config(cls.config_path)

        app.state.config = cfg
        app.state.session = sess
        app.state.scale_config = scale
        app.state.backup_config = backup
        app.state.sms_config = sms
        app.state.scale_service = None
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 1, "role": "admin", "iat": 9999999999
        }
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        import src.main as main_mod

        cls.temp_dir.cleanup()
        main_mod.CONFIG_PATH = cls.original_config_path

    def test_put_scale_config_valid(self):
        response = self.client.put(
            "/api/setup/scale",
            json={"timeout_seconds": 5},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["timeout_seconds"], 5)
        _, _, reloaded, _, _, _ = load_config(self.config_path)
        self.assertEqual(reloaded.timeout_seconds, 5)

    def test_put_scale_config_invalid_below_range(self):
        response = self.client.put(
            "/api/setup/scale",
            json={"timeout_seconds": 0},
        )
        self.assertEqual(response.status_code, 422)

    def test_put_scale_config_invalid_above_range(self):
        response = self.client.put(
            "/api/setup/scale",
            json={"timeout_seconds": 11},
        )
        self.assertEqual(response.status_code, 422)

    def test_put_scale_config_invalid_type(self):
        response = self.client.put(
            "/api/setup/scale",
            json={"timeout_seconds": "abc"},
        )
        self.assertEqual(response.status_code, 422)

    def test_put_scale_config_unauthorized(self):
        from src.auth import get_current_user
        import src.main as main_mod

        original = main_mod.app.dependency_overrides.pop(get_current_user, None)
        try:
            response = self.client.put(
                "/api/setup/scale",
                json={"timeout_seconds": 5},
            )
            self.assertEqual(response.status_code, 401)
        finally:
            if original:
                main_mod.app.dependency_overrides[get_current_user] = original

    def test_put_scale_config_forbidden(self):
        from src.auth import get_current_user
        import src.main as main_mod

        original_override = main_mod.app.dependency_overrides.get(get_current_user)
        main_mod.app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 2, "role": "operator", "iat": 9999999999
        }
        try:
            response = self.client.put(
                "/api/setup/scale",
                json={"timeout_seconds": 5},
            )
            self.assertEqual(response.status_code, 403)
        finally:
            if original_override:
                main_mod.app.dependency_overrides[get_current_user] = original_override
            else:
                del main_mod.app.dependency_overrides[get_current_user]


class TestScaleBugFixes(unittest.TestCase):
    """Regression tests for Bug #29 fixes."""

    def setUp(self):
        self.config = ScaleConfig(timeout_seconds=3)
        self.serial_config = mock.MagicMock()
        self.serial_config.path = "/dev/ttyACM0"
        self.serial_config.baudrate = 115200
        self.serial_config.parity = "N"
        self.serial_config.data_bits = 8
        self.serial_config.stop_bits = 1.0

    def _wait_for_recovery(self, service, received, timeout=3.0):
        """Wait for callback to receive 2+ data points with polling,
        then stop the service. Uses real time.sleep() so the background
        thread gets GIL time to process recovery."""
        start = time.time()
        while len(received) < 2 and time.time() - start < timeout:
            time.sleep(0.05)
        service.stop()

    @mock.patch("src.scale.serial.Serial")
    def test_async_reader_recovers_from_serial_error(self, mock_serial):
        """Bug 1: SerialException triggers recovery and reader continues."""
        instance = mock_serial.return_value
        instance.is_open = True
        read_count = [0]
        results = [
            b"01ST,1, 10.0,PT 0.0, 0,kg\r\n",
            serial.SerialException("Device busy"),
            b"01ST,1, 20.0,PT 0.0, 0,kg\r\n",
        ]

        def readline_side():
            idx = read_count[0]
            read_count[0] += 1
            if idx < len(results):
                val = results[idx]
                if isinstance(val, BaseException):
                    raise val
                return val
            return b""

        instance.readline.side_effect = readline_side

        # Patch time.sleep to make backoff instant in the reader thread.
        with mock.patch(
            "src.scale.time.sleep", side_effect=lambda s: None
        ):
            received = []

            def callback(data):
                received.append(data)

            service = ScaleService(self.config, self.serial_config)
            service.async_listener(callback)
            service.start()
            self._wait_for_recovery(service, received)

        self.assertGreaterEqual(len(received), 2)
        self.assertEqual(received[0]["net_weight"], 10.0)
        self.assertEqual(received[-1]["net_weight"], 20.0)
        # Verify _recover_serial was called (new serial.Serial() created)
        self.assertGreaterEqual(mock_serial.call_count, 2)

    @mock.patch("src.scale.serial.Serial")
    def test_async_reader_type_error_recovery(self, mock_serial):
        """Bug 1: TypeError in serial read triggers recovery."""
        instance = mock_serial.return_value
        instance.is_open = True
        read_count = [0]
        results = [
            b"01ST,1, 30.0,PT 0.0, 0,kg\r\n",
            TypeError("'NoneType' object cannot be interpreted "
                      "as an integer"),
            b"01ST,1, 40.0,PT 0.0, 0,kg\r\n",
        ]

        def readline_side():
            idx = read_count[0]
            read_count[0] += 1
            if idx < len(results):
                val = results[idx]
                if isinstance(val, BaseException):
                    raise val
                return val
            return b""

        instance.readline.side_effect = readline_side

        with mock.patch(
            "src.scale.time.sleep", side_effect=lambda s: None
        ):
            received = []

            def callback(data):
                received.append(data)

            service = ScaleService(self.config, self.serial_config)
            service.async_listener(callback)
            service.start()
            self._wait_for_recovery(service, received)

        self.assertGreaterEqual(len(received), 2)
        self.assertEqual(received[0]["net_weight"], 30.0)
        self.assertEqual(received[-1]["net_weight"], 40.0)

    @mock.patch("src.scale.serial.Serial")
    def test_async_queue_drains_before_stop(self, mock_serial):
        """Bug 2a: Queue is drained inside the while loop (callback fires
        before stop() is called)."""
        instance = mock_serial.return_value
        instance.readline.side_effect = [
            b"01ST,1, 50.0,PT 0.0, 0,kg\r\n",
            b"",
            StopIteration,
        ]
        instance.is_open = True

        callback_called_before_stop = False

        def callback(_data):
            nonlocal callback_called_before_stop
            callback_called_before_stop = True

        service = ScaleService(self.config, self.serial_config)
        service.async_listener(callback)
        service.start()
        # Wait for data to arrive (reader runs in background thread)
        time.sleep(0.3)
        # Check callback was called WITHOUT calling stop() first
        self.assertTrue(callback_called_before_stop,
                        "Callback should have been called before stop()")
        service.stop()


if __name__ == "__main__":
    unittest.main()
