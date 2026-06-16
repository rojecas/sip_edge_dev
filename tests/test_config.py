"""Tests for system config model and endpoints."""

import subprocess
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from src.config import (
    BackupConfig,
    ScaleConfig,
    SerialPortConfig,
    GsmConfig,
    SystemConfig,
    VALID_BAUDRATES,
    VALID_DATA_BITS,
    VALID_PARITY,
    VALID_STOP_BITS,
    VALID_TEST_PORTS,
    default_config,
    load_config,
    save_config,
    validate_config,
)


class TestSerialPortConfig(unittest.TestCase):
    def test_creation_defaults(self):
        cfg = SerialPortConfig(
            path="/dev/ttyACM0",
            baudrate=115200,
            parity="N",
            data_bits=8,
            stop_bits=1.0,
        )
        self.assertEqual(cfg.path, "/dev/ttyACM0")
        self.assertEqual(cfg.baudrate, 115200)
        self.assertEqual(cfg.parity, "N")
        self.assertEqual(cfg.data_bits, 8)
        self.assertEqual(cfg.stop_bits, 1.0)

    def test_immutability(self):
        cfg = SerialPortConfig(
            path="/dev/ttyACM0",
            baudrate=115200,
            parity="N",
            data_bits=8,
            stop_bits=1.0,
        )
        with self.assertRaises(Exception):
            cfg.baudrate = 9600


class TestLoadSaveConfig(unittest.TestCase):
    def test_load_defaults_when_no_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = f"{d}/config.yaml"
            config, session, scale, backup, sms = load_config(path)
            self.assertIsInstance(config, SystemConfig)
            self.assertEqual(config.rs485.path, "/dev/ttyACM0")
            self.assertEqual(config.rs485.baudrate, 115200)
            self.assertEqual(config.rs485.parity, "N")
            self.assertEqual(config.rs485.data_bits, 8)
            self.assertEqual(config.rs485.stop_bits, 1.0)
            self.assertEqual(config.rs232.path, "/dev/ttyACM1")
            self.assertEqual(config.gsm.modem_index, 0)
            self.assertIsInstance(scale, ScaleConfig)
            self.assertEqual(scale.timeout_seconds, 3)

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = f"{d}/config.yaml"
            config = default_config()
            save_config(config, path)
            loaded, session, scale, backup, sms = load_config(path)
            self.assertEqual(loaded.rs485.path, config.rs485.path)
            self.assertEqual(loaded.rs485.baudrate, config.rs485.baudrate)
            self.assertEqual(loaded.rs485.parity, config.rs485.parity)
            self.assertEqual(loaded.rs485.data_bits, config.rs485.data_bits)
            self.assertEqual(loaded.rs485.stop_bits, config.rs485.stop_bits)
            self.assertEqual(loaded.rs232.path, config.rs232.path)
            self.assertEqual(loaded.gsm.modem_index, config.gsm.modem_index)

    def test_atomic_write_does_not_corrupt(self):
        with tempfile.TemporaryDirectory() as d:
            path = f"{d}/config.yaml"
            config = default_config()
            save_config(config, path)
            self.assertTrue(__import__("os").path.exists(path))
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("rs485", content)

    def test_load_invalid_yaml_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            path = f"{d}/config.yaml"
            with open(path, "w") as f:
                f.write("invalid: [yaml: broken")
            config, session, scale, backup, sms = load_config(path)
            self.assertEqual(config.rs485.path, "/dev/ttyACM0")
            self.assertEqual(config.rs232.path, "/dev/ttyACM1")


class TestValidateConfig(unittest.TestCase):
    def _default_serial(self):
        return SerialPortConfig(
            path="/dev/ttyACM0",
            baudrate=115200,
            parity="N",
            data_bits=8,
            stop_bits=1.0,
        )

    def _default_config(self, **overrides):
        rs485 = self._default_serial()
        rs232 = SerialPortConfig(
            path="/dev/ttyACM1",
            baudrate=115200,
            parity="N",
            data_bits=8,
            stop_bits=1.0,
        )
        gsm = GsmConfig(modem_index=0)
        if "rs485" in overrides:
            rs485 = overrides["rs485"]
        if "rs232" in overrides:
            rs232 = overrides["rs232"]
        if "gsm" in overrides:
            gsm = overrides["gsm"]
        return SystemConfig(
            rs485=rs485,
            rs232=rs232,
            gsm=gsm,
            last_updated="2026-01-01T00:00:00",
        )

    def test_invalid_baudrate(self):
        bad = SerialPortConfig(
            path="/dev/ttyACM0", baudrate=9999, parity="N", data_bits=8, stop_bits=1.0
        )
        cfg = self._default_config(rs485=bad)
        with self.assertRaises(ValueError):
            validate_config(cfg)

    def test_invalid_data_bits(self):
        bad = SerialPortConfig(
            path="/dev/ttyACM0", baudrate=115200, parity="N", data_bits=9, stop_bits=1.0
        )
        cfg = self._default_config(rs485=bad)
        with self.assertRaises(ValueError):
            validate_config(cfg)

    def test_invalid_parity(self):
        bad = SerialPortConfig(
            path="/dev/ttyACM0", baudrate=115200, parity="X", data_bits=8, stop_bits=1.0
        )
        cfg = self._default_config(rs485=bad)
        with self.assertRaises(ValueError):
            validate_config(cfg)

    def test_invalid_stop_bits(self):
        bad = SerialPortConfig(
            path="/dev/ttyACM0", baudrate=115200, parity="N", data_bits=8, stop_bits=3.0
        )
        cfg = self._default_config(rs485=bad)
        with self.assertRaises(ValueError):
            validate_config(cfg)

    def test_invalid_modem_index(self):
        cfg = self._default_config(gsm=GsmConfig(modem_index=-1))
        with self.assertRaises(ValueError):
            validate_config(cfg)

    def test_valid_config_passes(self):
        cfg = self._default_config()
        validate_config(cfg)


class TestConfigEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from src.main import app
        from src.auth import get_current_user
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.original_config_path = None
        import src.main as main_mod
        cls.original_config_path = main_mod.CONFIG_PATH
        main_mod.CONFIG_PATH = f"{cls.temp_dir.name}/config.yaml"
        from src.config import default_config, save_config
        save_config(default_config(), main_mod.CONFIG_PATH)
        from src.config import load_config
        config, session, scale, backup, sms = load_config(main_mod.CONFIG_PATH)
        app.state.config = config
        app.state.session = session
        app.state.scale_config = scale
        app.state.backup_config = backup
        app.state.sms_config = sms
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 1, "role": "admin", "iat": 9999999999
        }
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()
        if cls.original_config_path is not None:
            import src.main as main_mod
            main_mod.CONFIG_PATH = cls.original_config_path

    def test_get_config_returns_200(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("rs485", data)
        self.assertIn("rs232", data)
        self.assertIn("gsm", data)
        self.assertIn("last_updated", data)

    def test_put_config_valid_returns_200(self):
        new_config = {
            "rs485": {
                "path": "/dev/ttyACM0",
                "baudrate": 9600,
                "parity": "E",
                "data_bits": 7,
                "stop_bits": 2.0,
            },
            "rs232": {
                "path": "/dev/ttyACM1",
                "baudrate": 115200,
                "parity": "N",
                "data_bits": 8,
                "stop_bits": 1.0,
            },
            "gsm": {"modem_index": 1},
        }
        response = self.client.put("/api/config", json=new_config)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["rs485"]["baudrate"], 9600)
        self.assertEqual(data["rs485"]["parity"], "E")
        self.assertEqual(data["gsm"]["modem_index"], 1)

    def test_put_config_invalid_baudrate_returns_422(self):
        bad_config = {
            "rs485": {
                "path": "/dev/ttyACM0",
                "baudrate": 9999,
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
        }
        response = self.client.put("/api/config", json=bad_config)
        self.assertEqual(response.status_code, 422)


class TestConfigTestEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from src.main import app
        from src.auth import get_current_user
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.original_config_path = None
        import src.main as main_mod
        cls.original_config_path = main_mod.CONFIG_PATH
        main_mod.CONFIG_PATH = f"{cls.temp_dir.name}/config.yaml"
        from src.config import default_config, save_config
        save_config(default_config(), main_mod.CONFIG_PATH)
        from src.config import load_config
        config, session, scale, backup, sms = load_config(main_mod.CONFIG_PATH)
        app.state.config = config
        app.state.session = session
        app.state.scale_config = scale
        app.state.backup_config = backup
        app.state.sms_config = sms
        app.dependency_overrides[get_current_user] = lambda: {
            "user_id": 1, "role": "admin", "iat": 9999999999
        }
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()
        if cls.original_config_path is not None:
            import src.main as main_mod
            main_mod.CONFIG_PATH = cls.original_config_path

    def test_test_rs485_serial_attempt(self):
        response = self.client.post("/api/config/test/rs485")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        if data["status"] == "fail":
            self.assertIn("detail", data)

    def test_test_rs232_serial_attempt(self):
        response = self.client.post("/api/config/test/rs232")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        if data["status"] == "fail":
            self.assertIn("detail", data)

    @mock.patch("subprocess.run")
    def test_test_gsm_mmcli_success(self, mock_run):
        mock_run.return_value = mock.MagicMock(
            returncode=0, stderr=b""
        )
        response = self.client.post("/api/config/test/gsm")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    @mock.patch("subprocess.run")
    def test_test_gsm_mmcli_failure(self, mock_run):
        mock_run.return_value = mock.MagicMock(
            returncode=1, stderr=b"error: modem not found"
        )
        response = self.client.post("/api/config/test/gsm")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "fail")

    def test_test_invalid_port_returns_404(self):
        response = self.client.post("/api/config/test/invalid")
        self.assertEqual(response.status_code, 404)
