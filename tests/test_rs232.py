"""Tests for RS232 transmission module."""

import os
import tempfile
import unittest
from unittest import mock

from src.rs232 import Rs232Error, send_frame


def _write_default_config(path: str) -> None:
    """Write a minimal default config.yaml for tests."""
    import yaml

    config = {
        "rs485": {
            "path": "/dev/ttyACM0",
            "baudrate": 115200,
            "parity": "N",
            "data_bits": 8,
            "stop_bits": 1.0,
        },
        "rs232": {
            "path": "/dev/ttyACM1",
            "baudrate": 115200,
            "parity": "N",
            "data_bits": 8,
            "stop_bits": 1.0,
        },
        "gsm": {"modem_index": 0},
        "last_updated": "2026-01-01T00:00:00+00:00",
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)


def _write_custom_config(path: str) -> None:
    """Write a config.yaml with non-default RS232 settings for testing."""
    import yaml

    config = {
        "rs485": {
            "path": "/dev/ttyACM0",
            "baudrate": 115200,
            "parity": "N",
            "data_bits": 8,
            "stop_bits": 1.0,
        },
        "rs232": {
            "path": "/dev/ttyUSB9",
            "baudrate": 9600,
            "parity": "E",
            "data_bits": 7,
            "stop_bits": 1.5,
        },
        "gsm": {"modem_index": 0},
        "last_updated": "2026-01-01T00:00:00+00:00",
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config, f)


class TestSendFrame(unittest.TestCase):
    def setUp(self):
        # Docker has DEV_MODE=true by default; tests need it disabled to exercise
        # serial code. Save and override; test_dev_mode_skips_serial re-enables it.
        self._saved_dev_mode = os.environ.get("DEV_MODE")
        os.environ["DEV_MODE"] = "false"
        self.frame_data = {
            "id": 42,
            "fecha": "2026-06-15",
            "hora": "10:30:00",
            "tractomula": "ABC123",
            "vagon": "ABC-123",
            "numero_guia": "G-789",
            "hacienda": {"id": 1, "codigo": "H001", "nombre": "Test"},
            "suerte": {"id": 1, "codigo_suerte": "A1"},
            "pesos": {
                "muestra": 1.5,
                "mineral": 0.8,
                "vegetal_extrano": 0.2,
            },
        }

    def tearDown(self):
        if self._saved_dev_mode is not None:
            os.environ["DEV_MODE"] = self._saved_dev_mode
        else:
            os.environ.pop("DEV_MODE", None)

    @mock.patch("serial.Serial")
    def test_csv_format_15_fields(self, mock_serial):
        """R2: Verify frame has exactly 15 comma-separated fields in correct order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            _write_default_config(config_path)
            send_frame(self.frame_data, config_path=config_path)

        mock_serial.return_value.write.assert_called_once()
        frame = mock_serial.return_value.write.call_args[0][0].decode("ascii")
        fields = frame.strip().split(",")
        self.assertEqual(
            len(fields), 15, f"Expected 15 fields, got {len(fields)}: {fields}"
        )
        self.assertEqual(fields[0], "42")
        self.assertEqual(fields[1], "2026-06-15")
        self.assertEqual(fields[2], "10:30:00")
        self.assertEqual(fields[3], "ABC-123")
        self.assertEqual(fields[4], "G-789")
        self.assertEqual(fields[5], "1.500")
        for i in range(6, 13):
            self.assertEqual(fields[i], "0", f"Field {i} should be 0, got {fields[i]}")
        self.assertEqual(fields[13], "0.200")
        self.assertEqual(fields[14], "0.800")

    @mock.patch("serial.Serial")
    def test_vagon_unmodified(self, mock_serial):
        """R3: Verify vagon value appears unchanged at position 4."""
        data = dict(self.frame_data)
        data["vagon"] = "VGN-001-AB"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            _write_default_config(config_path)
            send_frame(data, config_path=config_path)

        frame = mock_serial.return_value.write.call_args[0][0].decode("ascii")
        fields = frame.strip().split(",")
        self.assertEqual(fields[3], "VGN-001-AB")

    @mock.patch("serial.Serial")
    def test_crlf_termination(self, mock_serial):
        """R8: Verify frame ends with CRLF."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            _write_default_config(config_path)
            send_frame(self.frame_data, config_path=config_path)

        frame = mock_serial.return_value.write.call_args[0][0].decode("ascii")
        self.assertTrue(
            frame.endswith("\r\n"), f"Frame should end with CRLF: {frame!r}"
        )

    @mock.patch("serial.Serial")
    def test_guia_from_numero_guia(self, mock_serial):
        """R9: Verify numero_guia appears as Guia field (position 5)."""
        data = dict(self.frame_data)
        data["numero_guia"] = "GUIA-999"
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            _write_default_config(config_path)
            send_frame(data, config_path=config_path)

        frame = mock_serial.return_value.write.call_args[0][0].decode("ascii")
        fields = frame.strip().split(",")
        self.assertEqual(fields[4], "GUIA-999")

    @mock.patch("serial.Serial")
    def test_pesos_three_decimals(self, mock_serial):
        """R10: Verify weights are formatted with exactly 3 decimals."""
        data = dict(self.frame_data)
        data["pesos"] = {
            "muestra": 2.0,
            "mineral": 0.1234,
            "vegetal_extrano": 0.0,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            _write_default_config(config_path)
            send_frame(data, config_path=config_path)

        frame = mock_serial.return_value.write.call_args[0][0].decode("ascii")
        fields = frame.strip().split(",")
        self.assertEqual(fields[5], "2.000")
        self.assertEqual(fields[13], "0.000")
        self.assertEqual(fields[14], "0.123")

    @mock.patch("serial.Serial")
    def test_dev_mode_skips_serial(self, mock_serial):
        """R7: With DEV_MODE=true, send_frame returns without opening serial port."""
        with mock.patch.dict(os.environ, {"DEV_MODE": "true"}):
            send_frame(self.frame_data)
        mock_serial.assert_not_called()

    @mock.patch("serial.Serial")
    def test_config_loaded_and_used(self, mock_serial):
        """R4: Verify send_frame loads config from YAML and uses its params."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            _write_custom_config(config_path)
            send_frame(self.frame_data, config_path=config_path)

        mock_serial.assert_called_once_with(
            port="/dev/ttyUSB9",
            baudrate=9600,
            parity="E",
            bytesize=7,
            stopbits=1.5,
            timeout=1,
        )

    @mock.patch("serial.Serial")
    def test_error_on_port_unavailable(self, mock_serial):
        """R6: When serial.Serial raises SerialException, send_frame raises Rs232Error."""
        import serial

        mock_serial.side_effect = serial.SerialException("Port not found")
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            _write_default_config(config_path)
            with self.assertRaises(Rs232Error):
                send_frame(self.frame_data, config_path=config_path)


if __name__ == "__main__":
    unittest.main()
