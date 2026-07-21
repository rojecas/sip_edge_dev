"""Scale service for DINI ARGEO DFWLI-2 via RS485 serial."""

import logging
import queue
import threading
import time

import serial

logger = logging.getLogger(__name__)


class ScaleConnectionError(Exception):
    """No se puede abrir/cerrar el puerto serial."""


class ScaleTimeoutError(Exception):
    """No se recibio respuesta dentro del timeout."""


class ScaleProtocolError(Exception):
    """Respuesta inesperada o mal formada desde la balanza."""


def parse_extended_response(line: str) -> dict:
    """Parse extended weight string: 01ST,1, 0.0,PT 20.8, 0,kg"""
    stripped = line.strip()
    parts = stripped.split(",")
    if len(parts) != 6:
        raise ScaleProtocolError(
            f"Extended response requires 6 comma-separated fields, got {len(parts)}: {line!r}"
        )
    address = parts[0][:2]
    status_code = parts[0][2:4]
    net_weight = float(parts[2].strip())
    tare_part = parts[3].strip()
    tare_parts = tare_part.split(" ", 1)
    tare_indicator = tare_parts[0] if len(tare_parts) > 0 else ""
    tare_weight = float(tare_parts[1].strip()) if len(tare_parts) > 1 else 0.0
    piece_count = int(parts[4].strip())
    unit = parts[5].strip()
    return {
        "address": address,
        "status_code": status_code,
        "is_stable": status_code == "ST",
        "net_weight": net_weight,
        "tare_indicator": tare_indicator,
        "tare_weight": tare_weight,
        "piece_count": piece_count,
        "unit": unit,
    }


def parse_short_response(line: str) -> dict:
    """Parse short weight string: ST,GS, 0.0,kg (DFW06L format)."""
    stripped = line.strip()
    parts = [p.strip() for p in stripped.split(",")]
    if len(parts) != 4:
        raise ScaleProtocolError(
            f"Short response requires 4 comma-separated fields, got {len(parts)}: {line!r}"
        )
    # DFW06L format: ST,GS, -0.49,kg
    # Field 0: stability indicator (ST=stable, US=unstable)
    # Field 1: gross/net indicator (GS=gross, NT=net)
    # Field 2: weight value
    # Field 3: unit
    status_code = parts[0]
    gross_net = parts[1]
    weight = float(parts[2])
    unit = parts[3]
    return {
        "address": "00",
        "status_code": status_code,
        "is_stable": status_code == "ST",
        "gross_net": gross_net,
        "weight": weight,
        "unit": unit,
    }


def _parse_response(line: str) -> dict:
    """Route to extended or short parser based on field count."""
    stripped = line.strip()
    parts = stripped.split(",")
    if len(parts) == 6:
        return parse_extended_response(line)
    if len(parts) == 4:
        return parse_short_response(line)
    raise ScaleProtocolError(
        f"Unrecognized response format: {line!r}"
    )


class ScaleService:
    """Singleton service managing serial communication with the scale."""

    def __init__(self, config, serial_config, dev_mode=False):
        self._config = config
        self._serial_config = serial_config
        self._serial = None
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._async_queue = queue.Queue()
        self._callback = None
        self._timeout = config.timeout_seconds
        self._dev_mode = dev_mode
        self._command_active = False
        self._response_event = threading.Event()
        self._response_data = None

    def update_timeout(self, timeout_seconds: int) -> None:
        self._timeout = timeout_seconds
        if self._serial is not None and self._serial.is_open:
            self._serial.timeout = timeout_seconds

    def start(self) -> None:
        if self._dev_mode:
            logger.warning("DEV_MODE: scale serial port connection skipped")
            return
        try:
            self._serial = serial.Serial(
                port=self._serial_config.path,
                baudrate=self._serial_config.baudrate,
                parity=self._serial_config.parity,
                bytesize=self._serial_config.data_bits,
                stopbits=self._serial_config.stop_bits,
                timeout=self._timeout,
            )
        except (serial.SerialException, OSError) as e:
            logger.warning("Cannot open serial port %s: %s. Running without scale.", self._serial_config.path, e)
            self._running = False
            return

        self._thread = threading.Thread(target=self._async_reader, daemon=True)
        self._thread.start()
        logger.info("ScaleService started on %s", self._serial_config.path)

    def stop(self) -> None:
        self._running = False
        if self._serial is not None and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=2)
        logger.info("ScaleService stopped")

    def send_command(self, command: str, value: str = None) -> dict:
        cmd_map = {
            "READ": "READ",
            "TARE": "TARE",
            "TMAN": "TMAN",
            "ZERO": "ZERO",
            "CLEAR": "CLEAR",
        }
        if command not in cmd_map:
            raise ScaleProtocolError(f"Unknown command: {command}")
        base = cmd_map[command]
        if command == "TMAN":
            if not value:
                raise ScaleProtocolError("TMAN command requires a value")
            cmd_str = f"{base}{value}\r\n"
        else:
            cmd_str = f"{base}\r\n"
        self._response_event.clear()
        self._response_data = None
        self._command_active = True
        try:
            with self._lock:
                if self._serial is None or not self._serial.is_open:
                    raise ScaleConnectionError("Serial port not open")
                try:
                    self._serial.reset_input_buffer()
                    self._serial.write(cmd_str.encode("ascii"))
                    self._serial.flush()
                except (serial.SerialException, OSError) as e:
                    raise ScaleConnectionError(f"Write error: {e}") from e
            if not self._response_event.wait(timeout=self._timeout):
                raise ScaleTimeoutError(
                    f"No response within {self._timeout}s"
                )
            data = self._response_data
            if data is None:
                raise ScaleTimeoutError(
                    f"No response within {self._timeout}s"
                )
            if not isinstance(data, dict):
                raise ScaleProtocolError(
                    f"Unexpected response type: {type(data).__name__}"
                )
            return data
        finally:
            self._command_active = False

    def async_listener(self, callback) -> None:
        self._callback = callback

    def _recover_serial(self) -> bool:
        """Attempt to re-open serial port after an error.

        Returns True if reconnection succeeded, False otherwise.
        """
        try:
            if self._serial is not None:
                try:
                    if self._serial.is_open:
                        self._serial.close()
                except Exception:
                    pass
            self._serial = serial.Serial(
                port=self._serial_config.path,
                baudrate=self._serial_config.baudrate,
                parity=self._serial_config.parity,
                bytesize=self._serial_config.data_bits,
                stopbits=self._serial_config.stop_bits,
                timeout=self._timeout,
            )
            logger.info(
                "Serial port %s re-opened after error", self._serial_config.path
            )
            return True
        except (serial.SerialException, OSError) as e:
            logger.error(
                "Failed to re-open serial port %s: %s",
                self._serial_config.path, e,
            )
            return False

    def _async_reader(self) -> None:
        consecutive_errors = 0
        max_errors = 5
        backoff = 1  # seconds, doubles each attempt

        while self._running:
            try:
                if self._serial is not None and self._serial.is_open:
                    line = self._serial.readline()
                    if line:
                        decoded = line.decode("ascii", errors="replace").strip()
                        if decoded:
                            if decoded == "OK":
                                parsed = {"result": "ok"}
                            else:
                                try:
                                    parsed = _parse_response(decoded)
                                except ScaleProtocolError:
                                    logger.warning(
                                        "Ignoring unparseable async line: %s", decoded
                                    )
                                    parsed = None
                            if parsed is not None:
                                if self._command_active:
                                    self._response_data = parsed
                                    self._response_event.set()
                                else:
                                    self._async_queue.put(parsed)
                # Drain queue inside the while loop so callbacks fire in
                # real time (Bug 2a fix — was outside the loop before).
                self._process_async_queue()
                # Successful iteration → reset error counters
                consecutive_errors = 0
                backoff = 1
            except serial.SerialTimeoutException:
                # Timeout on readline is expected (no data within timeout).
                # Do NOT trigger port re-open for this; just continue.
                if self._running:
                    logger.debug("Async serial read timed out (no data)")
            except (serial.SerialException, OSError, TypeError) as e:
                if self._running:
                    logger.error(
                        "Async serial read error: %s. Attempting recovery "
                        "(attempt %d/%d)...",
                        e, consecutive_errors + 1, max_errors,
                    )
                    self._recover_serial()
                    consecutive_errors += 1
                    if consecutive_errors >= max_errors:
                        logger.critical(
                            "Max consecutive serial errors (%d) reached. "
                            "Async reader giving up.", max_errors,
                        )
                        break
                    time.sleep(backoff)
                    backoff = min(backoff * 2, 8)
            except Exception:
                logger.exception("Unexpected error in async reader")
            # Yield to other threads (original code had this at the end of
            # every iteration; removing it caused a tight CPU loop).
            time.sleep(0.05)
        # Drain remaining items on thread exit
        self._process_async_queue()

    def _process_async_queue(self) -> None:
        while not self._async_queue.empty():
            try:
                data = self._async_queue.get_nowait()
                if self._callback:
                    try:
                        self._callback(data)
                    except Exception:
                        logger.exception("Async callback error")
            except queue.Empty:
                break
