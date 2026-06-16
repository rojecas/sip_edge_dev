"""Transmision de datos de pesaje a PC externo via RS232."""

import logging
import os

logger = logging.getLogger(__name__)


class Rs232Error(Exception):
    """Error base para fallos de transmision RS232."""


def send_frame(
    frame_data: dict,
    format: str = "csv",
    config_path: str = "config.yaml",
) -> None:
    """Construye y transmite una trama CSV al puerto RS232 del PC externo.

    Si DEV_MODE esta activo, omite toda operacion de E/S serial. En modo
    normal, carga la configuracion del puerto RS232 desde config.yaml,
    construye una linea CSV de 15 campos con terminacion CRLF, abre el
    puerto serial, escribe la trama y cierra el puerto.

    Args:
        frame_data: Diccionario con datos del pesaje (id, fecha, hora,
            vagon, numero_guia, pesos con muestra/mineral/vegetal_extrano).
        format: Ignorado; solo existe formato CSV por compatibilidad.
        config_path: Ruta al archivo de configuracion YAML.

    Raises:
        Rs232Error: Si el puerto serial no esta disponible o falla la escritura.
    """
    dev_mode = os.environ.get("DEV_MODE", "false").lower() in ("true", "1", "yes")
    if dev_mode:
        return

    from src.config import load_config

    system_config, _, _, _, _ = load_config(config_path)
    rs232_cfg = system_config.rs232

    csv_line = (
        f"{frame_data['id']},"
        f"{frame_data['fecha']},"
        f"{frame_data['hora']},"
        f"{frame_data['vagon']},"
        f"{frame_data['numero_guia']},"
        f"{float(frame_data['pesos']['muestra']):.3f},"
        f"0,0,0,0,0,0,0,"
        f"{float(frame_data['pesos']['vegetal_extrano']):.3f},"
        f"{float(frame_data['pesos']['mineral']):.3f}"
        f"\r\n"
    )

    import serial

    try:
        ser = serial.Serial(
            port=rs232_cfg.path,
            baudrate=rs232_cfg.baudrate,
            parity=rs232_cfg.parity,
            bytesize=rs232_cfg.data_bits,
            stopbits=rs232_cfg.stop_bits,
            timeout=1,
        )
        try:
            ser.write(csv_line.encode("ascii"))
            ser.flush()
        finally:
            ser.close()
    except serial.SerialException as e:
        raise Rs232Error(f"RS232 transmission failed: {e}") from e
    except OSError as e:
        raise Rs232Error(f"RS232 port error: {e}") from e
