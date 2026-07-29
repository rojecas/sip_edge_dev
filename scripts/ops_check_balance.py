"""Monitorea saldo SIM via USSD y envia alerta SMS si esta bajo umbral."""

import logging
import os
import re
import subprocess
import sys
import time

logger = logging.getLogger("check_balance")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

THRESHOLD = 5000
ALERT_PHONES = ["3006117436", "3502490204"]
ALERT_MESSAGE = (
    "ALERTA SIP-Edge: Saldo SIM ${balance}. "
    "Recargue para evitar interrupcion del servicio SMS."
)
USSD_RETRIES = 3
SMS_WAIT_SECONDS = 45
POLL_INTERVAL = 5
SERVICE_NAME = "sip-edge"


def _get_modem_index():
    """Auto-detecta el indice del modem Quectel/EC25 via mmcli -L."""
    try:
        result = subprocess.run(
            ["mmcli", "-L"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                m = re.search(r"/Modem/(\d+)\s+\[.*?\]\s+(.+)", line)
                if m:
                    model = m.group(2).upper()
                    if "QUECTEL" in model or "EC25" in model:
                        idx = int(m.group(1))
                        logger.info("Modem detectado: indice %s (%s)", idx, m.group(2))
                        return idx
            logger.error("No se encontro modem Quectel/EC25: %s", result.stdout)
        else:
            logger.error("mmcli -L fallo (rc=%s)", result.returncode)
    except FileNotFoundError:
        logger.error("mmcli no encontrado")
    except subprocess.TimeoutExpired:
        logger.error("Timeout en mmcli -L")
    except OSError as exc:
        logger.error("Error ejecutando mmcli -L: %s", exc)
    return None


def _clean_sms(modem_index):
    """Borra todos los SMS del modem."""
    try:
        result = subprocess.run(
            ["sudo", "-n", "mmcli", "-m", str(modem_index), "--messaging-list-sms"],
            capture_output=True, text=True, timeout=10,
        )
        for sid in re.findall(r"/SMS/(\d+)", result.stdout):
            subprocess.run(
                ["sudo", "-n", "mmcli", "-m", str(modem_index),
                 f"--messaging-delete-sms={sid}"],
                capture_output=True, text=True, timeout=10,
            )
        logger.debug("SMS limpiados del modem %s", modem_index)
    except Exception as exc:
        logger.warning("Error limpiando SMS: %s", exc)


def _request_balance_ussd(modem_index):
    """Envia USSD *10#, espera SMS de Tigo, parsea y retorna saldo (int).

    Returns:
        int: saldo en pesos, o None si no se pudo obtener.
    """
    for attempt in range(USSD_RETRIES):
        try:
            result = subprocess.run(
                ["sudo", "-n", "mmcli", "-m", str(modem_index),
                 "--3gpp-ussd-initiate=*10#"],
                capture_output=True, text=True, timeout=20,
            )
            if "A continuacion" in result.stdout or "recibiras" in result.stdout:
                logger.info("USSD *10# enviado exitosamente (intento %s)", attempt + 1)
                break
            logger.warning("USSD respuesta inesperada: %s", result.stdout.strip()[:100])
        except subprocess.TimeoutExpired:
            logger.warning("Timeout en USSD (intento %s)", attempt + 1)
        except Exception as exc:
            logger.warning("Error en USSD (intento %s): %s", attempt + 1, exc)
        time.sleep(3)
    else:
        logger.error("No se pudo enviar USSD *10# tras %s intentos", USSD_RETRIES)
        return None

    logger.info("Esperando SMS de Tigo (max %ss)...", SMS_WAIT_SECONDS)
    deadline = time.time() + SMS_WAIT_SECONDS
    while time.time() < deadline:
        time.sleep(POLL_INTERVAL)
        try:
            result = subprocess.run(
                ["sudo", "-n", "mmcli", "-m", str(modem_index), "--messaging-list-sms"],
                capture_output=True, text=True, timeout=10,
            )
            sms_ids = re.findall(r"/SMS/(\d+)", result.stdout)
            if not sms_ids:
                continue

            for sid in sms_ids:
                try:
                    sms = subprocess.run(
                        ["sudo", "-n", "mmcli", "-s", sid],
                        capture_output=True, text=True, timeout=10,
                    )
                    number = _extract_field(sms.stdout, "number")
                    sms_text = _extract_field(sms.stdout, "text")
                    state = _extract_field(sms.stdout, "state")

                    if number and "TIGO" in number.upper() and sms_text:
                        saldo_match = re.search(r"Saldo:\s*(\d+)", sms_text)
                        if saldo_match:
                            saldo = int(saldo_match.group(1))
                            logger.info("Saldo encontrado en SMS %s: $%s", sid, saldo)
                            return saldo
                        logger.debug("SMS de Tigo sin saldo: %s", sms_text[:80])
                except Exception as exc:
                    logger.debug("Error leyendo SMS %s: %s", sid, exc)
        except Exception as exc:
            logger.debug("Error en polling SMS: %s", exc)

    logger.error("No se recibio SMS de saldo tras %ss", SMS_WAIT_SECONDS)
    return None


def _extract_field(mmcli_output, field):
    """Extrae valor de un campo de mmcli -s <ID>."""
    pattern = re.compile(
        r"\|\s*" + re.escape(field) + r"\s*:\s*(.+)$",
        re.MULTILINE,
    )
    match = pattern.search(mmcli_output)
    if match:
        return match.group(1).strip()
    return None


def _send_alert(modem_index, balance):
    """Envia SMS de alerta a los numeros configurados."""
    message = ALERT_MESSAGE.format(balance=balance)
    for phone in ALERT_PHONES:
        try:
            props = f"number='{phone}',text='{message}'"
            create = subprocess.run(
                ["sudo", "-n", "mmcli", "-m", str(modem_index),
                 "--messaging-create-sms", props],
                capture_output=True, text=True, timeout=15,
            )
            match = re.search(r"/SMS/(\d+)", create.stdout)
            if match:
                sid = match.group(1)
                send = subprocess.run(
                    ["sudo", "-n", "mmcli", "-s", sid, "--send"],
                    capture_output=True, text=True, timeout=30,
                )
                if "successfully" in send.stdout:
                    logger.info("Alerta SMS enviada a %s", phone)
                else:
                    logger.error("Fallo envio SMS a %s: %s", phone,
                                 send.stdout.strip()[:100])
            else:
                logger.error("No se pudo crear SMS para %s", phone)
        except Exception as exc:
            logger.error("Error enviando alerta a %s: %s", phone, exc)


def _stop_service():
    """Detiene el servicio sip-edge para que no procese los SMS de saldo."""
    try:
        subprocess.run(
            f"echo sipedge1234 | sudo -S systemctl stop {SERVICE_NAME}",
            capture_output=True, text=True, timeout=15, shell=True,
        )
        time.sleep(2)
        result = subprocess.run(
            ["systemctl", "is-active", SERVICE_NAME],
            capture_output=True, text=True, timeout=5,
        )
        if "inactive" in result.stdout:
            logger.info("Servicio %s detenido", SERVICE_NAME)
            return True
        logger.warning("No se pudo detener %s: %s", SERVICE_NAME, result.stdout.strip())
    except Exception as exc:
        logger.warning("Error deteniendo %s: %s", SERVICE_NAME, exc)
    return False


def _start_service():
    """Reinicia el servicio sip-edge."""
    try:
        subprocess.run(
            f"echo sipedge1234 | sudo -S systemctl start {SERVICE_NAME}",
            capture_output=True, text=True, timeout=15, shell=True,
        )
        logger.info("Servicio %s iniciado", SERVICE_NAME)
    except Exception as exc:
        logger.warning("Error iniciando %s: %s", SERVICE_NAME, exc)


def main():
    modem_index = _get_modem_index()
    if modem_index is None:
        logger.error("Modem no detectado. Abortando.")
        sys.exit(1)

    _stop_service()

    try:
        logger.info("Limpiando SMS viejos...")
        _clean_sms(modem_index)

        logger.info("Solicitando saldo via USSD *10#...")
        saldo = _request_balance_ussd(modem_index)

        _clean_sms(modem_index)

        if saldo is None:
            logger.error("No se pudo obtener el saldo.")
            sys.exit(1)

        logger.info("Saldo SIM: $%s", saldo)

        if saldo < THRESHOLD:
            logger.warning(
                "SALDO BAJO: $%s < $%s (umbral). Enviando alerta SMS...",
                saldo, THRESHOLD,
            )
            _send_alert(modem_index, saldo)
        else:
            logger.info("Saldo OK: $%s >= $%s", saldo, THRESHOLD)
    finally:
        _start_service()


if __name__ == "__main__":
    main()
