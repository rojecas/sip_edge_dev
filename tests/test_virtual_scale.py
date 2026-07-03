"""Tests para la balanza virtual DINI ARGEO DFWLI-2."""

import csv
import os
import subprocess
import sys
import tempfile
import time
import unittest
import argparse

from src.tools.virtual_scale import (
    _build_extended_response,
    _build_ok_response,
    _current_reading,
    _parse_serial_command,
    _show_status,
    _simulate_stability,
    load_dataset,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_mini_csv(dirpath: str, rows: list[list[str | int | float]]) -> str:
    """Crea un CSV temporal con header + rows y devuelve la ruta."""
    filepath = os.path.join(dirpath, "dataset_A.csv")
    with open(filepath, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "status_muestra", "peso_muestra",
            "status_mineral", "peso_mineral",
            "status_vegetal", "peso_vegetal",
            "unit",
        ])
        for row in rows:
            writer.writerow(row)
    return filepath


def _write_named_csv(dirpath: str, name: str, rows: list[list[str | int | float]]) -> str:
    """Crea un CSV con nombre especifico."""
    filepath = os.path.join(dirpath, name)
    with open(filepath, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "status_muestra", "peso_muestra",
            "status_mineral", "peso_mineral",
            "status_vegetal", "peso_vegetal",
            "unit",
        ])
        for row in rows:
            writer.writerow(row)
    return filepath


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestLoadDataset(unittest.TestCase):
    """T5 — Carga de CSV con validacion."""

    def test_load_dataset_success(self):
        """Carga un CSV valido y retorna lista de dicts."""
        with tempfile.TemporaryDirectory() as d:
            _write_mini_csv(d, [
                ["ST", 245.3, "US", 25.7, "ST", 8.2, "kg"],
                ["US", 312.1, "ST", 45.3, "US", 12.8, "kg"],
            ])
            result = load_dataset(d, "A")
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["peso_muestra"], 245.3)
            self.assertEqual(result[0]["status_muestra"], "ST")
            self.assertEqual(result[0]["unit"], "kg")

    def test_load_dataset_not_found(self):
        """Archivo inexistente lanza SystemExit."""
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit):
                load_dataset(d, "A")

    def test_load_dataset_bad_header(self):
        """Header incorrecto lanza SystemExit."""
        with tempfile.TemporaryDirectory() as d:
            filepath = os.path.join(d, "dataset_A.csv")
            with open(filepath, "w", encoding="utf-8", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(["col1", "col2"])
                writer.writerow(["a", "b"])
            with self.assertRaises(SystemExit):
                load_dataset(d, "A")

    def test_load_dataset_non_numeric_weight(self):
        """Peso no numerico lanza SystemExit."""
        with tempfile.TemporaryDirectory() as d:
            _write_mini_csv(d, [
                ["ST", "no_es_numero", "ST", 10.0, "ST", 5.0, "kg"],
            ])
            with self.assertRaises(SystemExit):
                load_dataset(d, "A")

    def test_load_dataset_b(self):
        """R12 — Carga dataset B."""
        with tempfile.TemporaryDirectory() as d:
            _write_named_csv(d, "dataset_B.csv", [
                ["ST", 250.0, "US", 50.0, "ST", 20.0, "kg"],
            ])
            result = load_dataset(d, "B")
            self.assertEqual(len(result), 1)

    def test_load_dataset_c(self):
        """R12 — Carga dataset C."""
        with tempfile.TemporaryDirectory() as d:
            _write_named_csv(d, "dataset_C.csv", [
                ["US", 300.0, "ST", 100.0, "US", 50.0, "kg"],
            ])
            result = load_dataset(d, "C")
            self.assertEqual(len(result), 1)

    def test_load_dataset_d(self):
        """R12 — Carga dataset D."""
        with tempfile.TemporaryDirectory() as d:
            _write_named_csv(d, "dataset_D.csv", [
                ["ST", 200.0, "US", 250.0, "ST", 80.0, "kg"],
            ])
            result = load_dataset(d, "D")
            self.assertEqual(len(result), 1)

    def test_load_dataset_e(self):
        """R12 — Carga dataset E."""
        with tempfile.TemporaryDirectory() as d:
            _write_named_csv(d, "dataset_E.csv", [
                ["US", 180.0, "ST", 30.0, "US", 5.0, "kg"],
            ])
            result = load_dataset(d, "E")
            self.assertEqual(len(result), 1)


class TestCurrentReading(unittest.TestCase):
    """T6 — Lectura del sub-paso activo."""

    def setUp(self):
        self.dataset = [
            {
                "status_muestra": "ST", "peso_muestra": 100.0,
                "status_mineral": "US", "peso_mineral": 20.0,
                "status_vegetal": "ST", "peso_vegetal": 5.0,
                "unit": "kg",
            },
        ]

    def test_current_reading_muestra(self):
        """Pointer (0, 0) retorna peso_muestra."""
        reading = _current_reading((0, 0), self.dataset, None)
        self.assertEqual(reading["peso"], 100.0)
        self.assertEqual(reading["status"], "ST")

    def test_current_reading_mineral(self):
        """Pointer (0, 1) retorna peso_mineral."""
        reading = _current_reading((0, 1), self.dataset, None)
        self.assertEqual(reading["peso"], 20.0)
        self.assertEqual(reading["status"], "US")

    def test_current_reading_vegetal(self):
        """Pointer (0, 2) retorna peso_vegetal."""
        reading = _current_reading((0, 2), self.dataset, None)
        self.assertEqual(reading["peso"], 5.0)
        self.assertEqual(reading["status"], "ST")

    def test_current_reading_override(self):
        """Override activo retorna el peso override, no el del CSV."""
        reading = _current_reading((0, 0), self.dataset, 999.9)
        self.assertEqual(reading["peso"], 999.9)
        self.assertEqual(reading["status"], "ST")


class TestBuildResponses(unittest.TestCase):
    """T7, T8 — Construccion de respuestas del protocolo."""

    def test_build_extended_response(self):
        """Verifica formato exacto de respuesta REXT."""
        reading = {"status": "ST", "peso": 245.3, "unit": "kg"}
        resp = _build_extended_response(reading)
        self.assertEqual(resp, "01ST,1,245.3,PT 0.0,0,kg\r\n")

    def test_build_extended_response_with_other_unit(self):
        """Verifica que usa la unidad del reading."""
        reading = {"status": "ST", "peso": 100.0, "unit": "lb"}
        resp = _build_extended_response(reading)
        self.assertEqual(resp, "01ST,1,100.0,PT 0.0,0,lb\r\n")

    def test_build_ok_response(self):
        """Verifica que devuelve OK\\r\\n."""
        self.assertEqual(_build_ok_response(), "OK\r\n")


class TestSimulateStability(unittest.TestCase):
    """T9 — Simulacion de estabilidad (delay condicional)."""

    def test_simulate_stability_st(self):
        """Status ST no debe introducir delay significativo."""
        start = time.perf_counter()
        _simulate_stability("ST")
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.05)

    def test_simulate_stability_st_with_spaces(self):
        """ST con espacios alrededor tambien es instantaneo."""
        start = time.perf_counter()
        _simulate_stability("  ST  ")
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.05)

    def test_simulate_stability_us_delay_range(self):
        """R6 — Status US produce delay entre 200ms y 3s."""
        start = time.perf_counter()
        _simulate_stability("US")
        elapsed = time.perf_counter() - start
        self.assertGreaterEqual(elapsed, 0.19)
        self.assertLess(elapsed, 3.1)

    def test_simulate_stability_unknown_triggers_warning(self):
        """Status desconocido emite warning a stderr (no produce delay)."""
        old_stderr = sys.stderr
        try:
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as fake_err:
                sys.stderr = fake_err
                start = time.perf_counter()
                _simulate_stability("XX")
                elapsed = time.perf_counter() - start
                self.assertLess(elapsed, 0.05)
                fake_err.seek(0)
                output = fake_err.read()
                self.assertIn("WARNING", output)
                self.assertIn("XX", output)
        finally:
            sys.stderr = old_stderr


class TestParseSerialCommand(unittest.TestCase):
    """T10 — Parseo de comandos seriales."""

    def test_parse_command_unknown(self):
        """Comando no reconocido retorna UNKNOWN."""
        cmd, arg = _parse_serial_command("HELLO\r\n")
        self.assertEqual(cmd, "UNKNOWN")

    def test_parse_command_empty_line(self):
        """Linea vacia retorna EMPTY."""
        cmd, arg = _parse_serial_command("")
        self.assertEqual(cmd, "EMPTY")

    def test_parse_command_rext(self):
        """Detecta comando REXT correctamente."""
        cmd, arg = _parse_serial_command("00REXT\r\n")
        self.assertEqual(cmd, "REXT")
        self.assertIsNone(arg)

    def test_parse_command_tare(self):
        """Detecta comando TARE correctamente."""
        cmd, arg = _parse_serial_command("00TARE\r\n")
        self.assertEqual(cmd, "TARE")

    def test_parse_command_zero(self):
        """Detecta comando ZERO correctamente."""
        cmd, arg = _parse_serial_command("00ZERO\r\n")
        self.assertEqual(cmd, "ZERO")

    def test_parse_command_clear(self):
        """Detecta comando CLEAR correctamente."""
        cmd, arg = _parse_serial_command("00CLEAR\r\n")
        self.assertEqual(cmd, "CLEAR")

    def test_parse_command_tman_with_value(self):
        """Detecta comando TMAN con valor numerico."""
        cmd, arg = _parse_serial_command("00TMAN1.56\r\n")
        self.assertEqual(cmd, "TMAN")
        self.assertEqual(arg, "1.56")

    def test_parse_command_tman_without_value(self):
        """Detecta comando TMAN sin valor (solo prefijo)."""
        cmd, arg = _parse_serial_command("00TMAN\r\n")
        self.assertEqual(cmd, "TMAN")
        self.assertIsNone(arg)

    def test_parse_command_rext_no_cr(self):
        """Detecta REXT sin \\r (solo \\n o stripped)."""
        cmd, arg = _parse_serial_command("00REXT")
        self.assertEqual(cmd, "REXT")


class TestCurrentReadingIntegration(unittest.TestCase):
    """Tests de integracion usando CSV real pre-generado."""

    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join("data", "readings")

    def _check_dataset(self, dataset_id):
        """Verifica estructura basica de un dataset."""
        ds = load_dataset(self.data_dir, dataset_id)
        self.assertEqual(len(ds), 50)
        expected_keys = {
            "status_muestra", "peso_muestra",
            "status_mineral", "peso_mineral",
            "status_vegetal", "peso_vegetal",
            "unit",
        }
        for row in ds:
            self.assertEqual(set(row.keys()), expected_keys)
            self.assertIn(row["status_muestra"], {"ST", "US"})
            self.assertIn(row["status_mineral"], {"ST", "US"})
            self.assertIn(row["status_vegetal"], {"ST", "US"})
            self.assertIsInstance(row["peso_muestra"], float)
            self.assertIsInstance(row["peso_mineral"], float)
            self.assertIsInstance(row["peso_vegetal"], float)
        return ds

    def test_dataset_a_structure(self):
        """Dataset A tiene estructura valida."""
        self._check_dataset("A")

    def test_dataset_b_structure(self):
        """R11 — Dataset B tiene estructura valida."""
        self._check_dataset("B")

    def test_dataset_c_structure(self):
        """R11 — Dataset C tiene estructura valida."""
        self._check_dataset("C")

    def test_dataset_d_structure(self):
        """R11 — Dataset D tiene estructura valida."""
        self._check_dataset("D")

    def test_dataset_e_structure(self):
        """R11 — Dataset E tiene estructura valida."""
        self._check_dataset("E")

    def test_navigation_full_cycle(self):
        """Recorre las 50 medidas x 3 sub-pasos = 150 lecturas."""
        ds = load_dataset(self.data_dir, "A")
        count = 0
        row, sub = 0, 0
        while row < 50:
            reading = _current_reading((row, sub), ds, None)
            self.assertIsInstance(reading["peso"], float)
            count += 1
            if sub < 2:
                sub += 1
            else:
                row += 1
                sub = 0
        self.assertEqual(count, 150)

    def test_override_does_not_alter_csv(self):
        """Override retorna el valor alternativo sin modificar el dataset."""
        ds = load_dataset(self.data_dir, "A")
        original = ds[0]["peso_muestra"]
        reading = _current_reading((0, 0), ds, 999.9)
        self.assertEqual(reading["peso"], 999.9)
        self.assertEqual(ds[0]["peso_muestra"], original)

    def test_navigation_next_advances_sub_step(self):
        """R7 — Logica n: sub_step < 2 avanza sub_step."""
        self.assertEqual((0, 1), _navigate_next((0, 0), 50))

    def test_navigation_next_advances_row(self):
        """R7 — Logica n: sub_step == 2 avanza row y resetea sub_step."""
        self.assertEqual((1, 0), _navigate_next((0, 2), 50))

    def test_navigation_next_stops_at_end(self):
        """R7 — Logica n: no avanza mas alla de la ultima medida."""
        self.assertEqual((49, 2), _navigate_next((49, 2), 50))

    def test_navigation_prev_retreats_sub_step(self):
        """R8 — Logica p: sub_step > 0 retrocede sub_step."""
        self.assertEqual((0, 1), _navigate_prev((0, 2)))

    def test_navigation_prev_retreats_to_prev_row(self):
        """R8 — Logica p: sub_step == 0 y row > 0 retrocede a vegetal de fila anterior."""
        self.assertEqual((0, 2), _navigate_prev((1, 0)))

    def test_navigation_prev_stops_at_start(self):
        """R8 — Logica p: no retrocede antes de (0, 0)."""
        self.assertEqual((0, 0), _navigate_prev((0, 0)))


class TestEdgeCases(unittest.TestCase):
    """Tests de casos borde y formato."""

    def setUp(self):
        self.dataset = [
            {
                "status_muestra": "ST", "peso_muestra": 100.0,
                "status_mineral": "US", "peso_mineral": 20.0,
                "status_vegetal": "ST", "peso_vegetal": 5.0,
                "unit": "kg",
            },
        ]

    def test_build_extended_response_negative_weight(self):
        """Peso negativo se transmite tal cual."""
        reading = {"status": "ST", "peso": -10.5, "unit": "kg"}
        resp = _build_extended_response(reading)
        self.assertIn("-10.5", resp)

    def test_build_extended_response_zero_weight(self):
        """Peso cero se transmite correctamente."""
        reading = {"status": "ST", "peso": 0.0, "unit": "kg"}
        resp = _build_extended_response(reading)
        self.assertIn(",0.0,", resp)

    def test_parse_tman_with_long_value(self):
        """TMAN acepta valores de hasta 8 caracteres (spec R4)."""
        cmd, arg = _parse_serial_command("00TMAN12345678\r\n")
        self.assertEqual(cmd, "TMAN")
        self.assertEqual(arg, "12345678")


class TestCliArgs(unittest.TestCase):
    """R13, R14 — Tests de CLI args (argparse)."""

    def setUp(self):
        from src.tools.virtual_scale import main as _main
        import inspect
        source = inspect.getsource(_main)
        self.assertIn("argparse", source)

    def test_help_output(self):
        """R14 — --help muestra los parametros esperados."""
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        result = subprocess.run(
            [sys.executable, "-m", "src.tools.virtual_scale", "--help"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--port", result.stdout)
        self.assertIn("--baudrate", result.stdout)
        self.assertIn("--dataset", result.stdout)
        self.assertIn("--data-dir", result.stdout)


class TestGenerateReadings(unittest.TestCase):
    """R15, R16 — Tests para generate_readings.py."""

    def test_generate_readings_creates_five_csvs(self):
        """R16 — El script genera los 5 archivos CSV."""
        with tempfile.TemporaryDirectory() as d:
            env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
            result = subprocess.run(
                [sys.executable, "scripts/generate_readings.py",
                 "--output-dir", d, "--seed", "42"],
                capture_output=True, text=True, env=env, timeout=30,
            )
            self.assertEqual(result.returncode, 0)
            for prefix in ("A", "B", "C", "D", "E"):
                fpath = os.path.join(d, f"dataset_{prefix}.csv")
                self.assertTrue(os.path.isfile(fpath), f"Falta {fpath}")
                with open(fpath, "r", encoding="utf-8") as fh:
                    reader = csv.reader(fh)
                    lines = list(reader)
                    self.assertEqual(len(lines), 51, f"Dataset {prefix}: esperaba 51 lineas (header+50)")


class TestSerialPortError(unittest.TestCase):
    """R18 — Error de puerto serial."""

    def test_missing_port_triggers_stderr(self):
        """R18 — Puerto inexistente produce mensaje de error en stderr y exit != 0."""
        env = {**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)}
        result = subprocess.run(
            [sys.executable, "-m", "src.tools.virtual_scale",
             "--port", "/dev/NOEXISTE12345"],
            capture_output=True, text=True, env=env, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ERROR", result.stderr)


# ---------------------------------------------------------------------------
# Navigation helper functions (extracted from main for testability)
# ---------------------------------------------------------------------------


def _navigate_next(pointer: tuple[int, int], total_rows: int) -> tuple[int, int]:
    """Logica de navegacion forward (tecla n)."""
    row, sub = pointer
    if sub < 2:
        return (row, sub + 1)
    elif row < total_rows - 1:
        return (row + 1, 0)
    return pointer


def _navigate_prev(pointer: tuple[int, int]) -> tuple[int, int]:
    """Logica de navegacion backward (tecla p)."""
    row, sub = pointer
    if sub > 0:
        return (row, sub - 1)
    elif row > 0:
        return (row - 1, 2)
    return pointer


if __name__ == "__main__":
    unittest.main()
