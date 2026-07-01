"""Tests for sms_incoming: IncomingSmsDispatcher and _extract_sms_field."""

import asyncio
import unittest
from unittest import mock

from src.sms_incoming import IncomingSmsDispatcher, _extract_sms_field


# ==================================================================
# _extract_sms_field tests
# ==================================================================


class TestExtractSmsField(unittest.TestCase):
    """Tests para _extract_sms_field: extraccion de campos de mmcli output."""

    _MMCLI_OUTPUT = """  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: received
             |     number: +573001234567
             |       text: Hello world
"""

    def test_extract_state_received(self):
        """Extraer 'state: received' del mmcli output."""
        result = _extract_sms_field(self._MMCLI_OUTPUT, "state")
        self.assertEqual(result, "received")

    def test_extract_state_sent(self):
        """Extraer 'state: sent' del mmcli output."""
        output = """  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: sent
             |     number: +573001234567
             |       text: Hello world
"""
        result = _extract_sms_field(output, "state")
        self.assertEqual(result, "sent")

    def test_extract_state_stored(self):
        """Extraer 'state: stored' del mmcli output."""
        output = """  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: stored
             |     number: +573001234567
             |       text: Hello world
"""
        result = _extract_sms_field(output, "state")
        self.assertEqual(result, "stored")

    def test_extract_number(self):
        """Extraer 'number' del mmcli output."""
        result = _extract_sms_field(self._MMCLI_OUTPUT, "number")
        self.assertEqual(result, "+573001234567")

    def test_extract_text(self):
        """Extraer 'text' del mmcli output."""
        result = _extract_sms_field(self._MMCLI_OUTPUT, "text")
        self.assertEqual(result, "Hello world")

    def test_extract_status_returns_none(self):
        """BUG #26: 'status' NO existe en mmcli output, debe retornar None.
        El campo real se llama 'state', no 'status'. Este test documenta
        el error que causa que SMS salientes no sean filtrados."""
        result = _extract_sms_field(self._MMCLI_OUTPUT, "status")
        self.assertIsNone(result)

    def test_extract_nonexistent_field_returns_none(self):
        """Campo inexistente retorna None."""
        result = _extract_sms_field("some random output", "nonexistent")
        self.assertIsNone(result)

    def test_extract_field_empty_output(self):
        """Output vacio retorna None."""
        result = _extract_sms_field("", "state")
        self.assertIsNone(result)

    def test_extract_field_no_match(self):
        """Output sin formato mmcli retorna None."""
        result = _extract_sms_field("line1\nline2\n", "state")
        self.assertIsNone(result)


# ==================================================================
# IncomingSmsDispatcher _fetch_mmcli_sms filter tests
# ==================================================================


class TestFetchMmcliSmsFiltering(unittest.TestCase):
    """Tests para _fetch_mmcli_sms: verificar que SMS salientes
    (state=sent/stored) son filtrados y no llegan al codigo de
    negocio.

    BUG #26: Antes del fix, _extract_sms_field(read.stdout, "status")
    retornaba None porque mmcli usa "state", por lo que el filtro
    nunca se activaba y SMS salientes se procesaban como entrantes.

    Estos tests mockan subprocess.run para simular la salida de mmcli
    y verifican que _fetch_mmcli_sms retorne solo los SMS con
    state='received'.
    """

    def setUp(self):
        self.dispatcher = IncomingSmsDispatcher(modem_index=0, dev_mode=False)

    def _run_fetch(self) -> list[tuple[str, str]]:
        """Ejecuta _fetch_mmcli_sms de forma sincrona y retorna mensajes."""
        return asyncio.run(self.dispatcher._fetch_mmcli_sms())

    @mock.patch("src.sms_incoming.subprocess.run")
    def test_sent_sms_is_filtered(self, mock_run):
        """BUG #26: SMS con state='sent' NO debe estar en los mensajes retornados."""
        list_result = mock.MagicMock()
        list_result.returncode = 0
        list_result.stdout = "/org/freedesktop/ModemManager1/SMS/1\n"

        read_result = mock.MagicMock()
        read_result.returncode = 0
        read_result.stdout = """  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: sent
             |     number: +573001234567
             |       text: SIP-Edge solicitud emergencia
"""
        delete_result = mock.MagicMock()
        delete_result.returncode = 0
        delete_result.stdout = ""

        mock_run.side_effect = [list_result, read_result, delete_result]

        messages = self._run_fetch()

        self.assertEqual(
            len(messages), 0,
            "SMS 'sent' no debe estar en mensajes retornados",
        )

    @mock.patch("src.sms_incoming.subprocess.run")
    def test_stored_sms_is_filtered(self, mock_run):
        """SMS con state='stored' NO debe estar en los mensajes retornados."""
        list_result = mock.MagicMock()
        list_result.returncode = 0
        list_result.stdout = "/org/freedesktop/ModemManager1/SMS/2\n"

        read_result = mock.MagicMock()
        read_result.returncode = 0
        read_result.stdout = """  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: stored
             |     number: +573001234567
             |       text: Test
"""
        delete_result = mock.MagicMock()
        delete_result.returncode = 0
        delete_result.stdout = ""

        mock_run.side_effect = [list_result, read_result, delete_result]

        messages = self._run_fetch()

        self.assertEqual(
            len(messages), 0,
            "SMS 'stored' no debe estar en mensajes retornados",
        )

    @mock.patch("src.sms_incoming.subprocess.run")
    def test_received_sms_passes_filter(self, mock_run):
        """SMS con state='received' DEBE estar en los mensajes retornados."""
        list_result = mock.MagicMock()
        list_result.returncode = 0
        list_result.stdout = "/org/freedesktop/ModemManager1/SMS/3\n"

        read_result = mock.MagicMock()
        read_result.returncode = 0
        read_result.stdout = """  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: received
             |     number: +573001234567
             |       text: manual on
"""
        delete_result = mock.MagicMock()
        delete_result.returncode = 0
        delete_result.stdout = ""

        mock_run.side_effect = [list_result, read_result, delete_result]

        messages = self._run_fetch()

        self.assertEqual(
            len(messages), 1,
            "SMS 'received' debe estar en mensajes retornados",
        )
        self.assertEqual(messages[0][0], "+573001234567")
        self.assertEqual(messages[0][1], "manual on")

    @mock.patch("src.sms_incoming.subprocess.run")
    def test_received_sms_with_special_chars(self, mock_run):
        """SMS received con texto debe pasar el filtro."""
        list_result = mock.MagicMock()
        list_result.returncode = 0
        list_result.stdout = "/org/freedesktop/ModemManager1/SMS/4\n"

        read_result = mock.MagicMock()
        read_result.returncode = 0
        read_result.stdout = """  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: received
             |     number: +573009999999
             |       text: manual on ext 2h
"""
        delete_result = mock.MagicMock()
        delete_result.returncode = 0
        delete_result.stdout = ""

        mock_run.side_effect = [list_result, read_result, delete_result]

        messages = self._run_fetch()

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0][1], "manual on ext 2h")

    @mock.patch("src.sms_incoming.subprocess.run")
    def test_mixed_sms_only_received_processed(self, mock_run):
        """Multiple SMS: solo los 'received' deben retornarse."""
        list_result = mock.MagicMock()
        list_result.returncode = 0
        list_result.stdout = (
            "/org/freedesktop/ModemManager1/SMS/1\n"
            "/org/freedesktop/ModemManager1/SMS/2\n"
            "/org/freedesktop/ModemManager1/SMS/3\n"
        )

        # SMS 1: sent
        read_1 = mock.MagicMock()
        read_1.returncode = 0
        read_1.stdout = """  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: sent
             |     number: +573001111111
             |       text: Outgoing message
"""
        # SMS 2: received
        read_2 = mock.MagicMock()
        read_2.returncode = 0
        read_2.stdout = """  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: received
             |     number: +573002222222
             |       text: manual on
"""
        # SMS 3: stored
        read_3 = mock.MagicMock()
        read_3.returncode = 0
        read_3.stdout = """  -------------------------------
  SMS (org.freedesktop.ModemManager1.SMS)
  -------------------------------
  Properties |       state: stored
             |     number: +573003333333
             |       text: Old stored message
"""
        delete_result = mock.MagicMock()
        delete_result.returncode = 0
        delete_result.stdout = ""

        mock_run.side_effect = [
            list_result,
            read_1, delete_result,  # SMS 1: read + delete (filtered)
            read_2, delete_result,  # SMS 2: read + delete (processed)
            read_3, delete_result,  # SMS 3: read + delete (filtered)
        ]

        messages = self._run_fetch()

        # Solo el SMS 2 (received) debe retornarse
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0][0], "+573002222222")
        self.assertEqual(messages[0][1], "manual on")


if __name__ == "__main__":
    unittest.main()
