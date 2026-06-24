"""Dispatcher compartido de SMS entrantes via ModemManager.

Centraliza el polling de mmcli para que multiples modulos (emergency_mode,
password_reset) puedan recibir SMS entrantes sin competir por el modem.
"""

import asyncio
import logging
import re
import subprocess
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)

_SMS_ID_RE = re.compile(r"/org/freedesktop/ModemManager1/SMS/(\d+)")


@runtime_checkable
class SmsHandler(Protocol):
    """Protocolo para handlers de SMS entrantes.

    Cada handler recibe (sender_phone, text) y retorna True si el SMS fue
    procesado. Si un handler retorna True, los handlers siguientes no se
    ejecutan para ese SMS.
    """

    def __call__(self, sender_phone: str, text: str) -> bool:
        ...


class IncomingSmsDispatcher:
    """Dispatcher centralizado de SMS entrantes.

    Ejecuta un unico bucle asyncio que consulta mmcli cada 15 segundos
    y distribuye los SMS a los handlers registrados en orden FIFO.
    En modo desarrollo, consume de una cola interna.
    """

    def __init__(self, modem_index: int, dev_mode: bool = False) -> None:
        self._modem_index = modem_index
        self._dev_mode = dev_mode
        self._handlers: list[SmsHandler] = []
        self._dev_queue: list[tuple[str, str]] = []
        self._poll_task: asyncio.Task | None = None

    def register_handler(self, handler: SmsHandler) -> None:
        """Registra un handler de SMS en el orden de llamada."""
        self._handlers.append(handler)
        logger.debug("IncomingSmsDispatcher: handler %s registrado", handler)

    def enqueue_incoming_sms(self, sender_phone: str, text: str) -> None:
        """Encola un SMS entrante simulado (para dev mode y tests)."""
        self._dev_queue.append((sender_phone, text))

    async def start(self) -> None:
        """Inicia el bucle de polling asyncio."""
        if self._poll_task is not None and not self._poll_task.done():
            logger.warning("IncomingSmsDispatcher: polling ya esta corriendo")
            return
        logger.info("IncomingSmsDispatcher: iniciando polling de SMS")
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Cancela el bucle de polling."""
        if self._poll_task is not None and not self._poll_task.done():
            logger.info("IncomingSmsDispatcher: deteniendo polling de SMS")
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
        self._poll_task = None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        """Bucle principal: cada 15 segundos consulta SMS entrantes."""
        while True:
            try:
                await self._check_incoming_sms()
            except asyncio.CancelledError:
                logger.info("IncomingSmsDispatcher: polling cancelado")
                break
            except Exception:
                logger.exception("Error en polling de SMS entrantes")
            try:
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                logger.info("IncomingSmsDispatcher: polling cancelado durante sleep")
                break

    async def _check_incoming_sms(self) -> None:
        """Verifica si hay SMS entrantes y los distribuye a los handlers."""
        messages: list[tuple[str, str]] = []

        if self._dev_mode:
            # En desarrollo: consumir de la cola interna
            while self._dev_queue:
                messages.append(self._dev_queue.pop(0))
        else:
            # En produccion: consultar mmcli
            mmcli_msgs = await self._fetch_mmcli_sms()
            messages.extend(mmcli_msgs)

        for sender_phone, text in messages:
            self._dispatch(sender_phone, text)

    async def _fetch_mmcli_sms(self) -> list[tuple[str, str]]:
        """Consulta mmcli para listar y leer SMS entrantes.

        Retorna una lista de tuplas (sender_phone, text) y elimina
        los SMS del modem tras procesarlos.
        """
        messages: list[tuple[str, str]] = []
        try:
            # 1. Listar SMS
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "sudo", "-n", "mmcli", "-m", str(self._modem_index),
                    "--messaging-list-sms",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                logger.warning(
                    "mmcli list-sms failed: %s",
                    (result.stderr or "").strip(),
                )
                return messages

            # 2. Extraer IDs y procesar cada SMS
            sms_ids = _SMS_ID_RE.findall(result.stdout)
            for sms_id in sms_ids:
                try:
                    read = await asyncio.to_thread(
                        subprocess.run,
                        ["sudo", "-n", "mmcli", "-s", sms_id],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if read.returncode != 0:
                        # Eliminar SMS problematico
                        await self._delete_sms(sms_id)
                        continue

                    sender = _extract_sms_field(read.stdout, "number")
                    text = _extract_sms_field(read.stdout, "text")
                    if sender and text:
                        messages.append((sender, text))

                    # 3. Eliminar SMS procesado
                    await self._delete_sms(sms_id)
                except Exception:
                    logger.exception("Error processing SMS id=%s", sms_id)
        except subprocess.TimeoutExpired:
            logger.warning("mmcli SMS polling timed out")
        except FileNotFoundError:
            if not self._dev_mode:
                logger.warning("mmcli not found, SMS polling disabled")
        except OSError as exc:
            logger.error("OS error during mmcli SMS polling: %s", exc)

        return messages

    async def _delete_sms(self, sms_id: str) -> None:
        """Elimina un SMS del modem por su ID."""
        try:
            await asyncio.to_thread(
                subprocess.run,
                ["sudo", "-n", "mmcli", "-m", str(self._modem_index), f"--messaging-delete-sms={sms_id}"],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            logger.warning("Failed to delete SMS id=%s", sms_id)

    def _dispatch(self, sender_phone: str, text: str) -> None:
        """Distribuye un SMS a los handlers en orden de registro.

        Si un handler retorna True, los handlers restantes no se ejecutan.
        Si ningun handler retorna True, el SMS se descarta silenciosamente.
        """
        for handler in self._handlers:
            try:
                if handler(sender_phone, text):
                    logger.debug("SMS handled by %s", handler)
                    return
            except Exception:
                logger.exception("Handler %s fallo procesando SMS", handler)
        logger.debug("SMS no manejado por ningun handler: %s", text[:50])


def _extract_sms_field(mmcli_output: str, field: str) -> str | None:
    """Extrae el valor de un campo de la salida de mmcli -s <id>."""
    pattern = re.compile(
        r"^\s*" + re.escape(field) + r"\s*\|\s*(.+?)(?:\s*\[.*?\])?\s*$",
        re.MULTILINE,
    )
    match = pattern.search(mmcli_output)
    if match:
        return match.group(1).strip()
    # Fallback: formato sin pipes
    pattern2 = re.compile(
        r"^\s*" + re.escape(field) + r"\s*:\s*(.+)$", re.MULTILINE
    )
    match2 = pattern2.search(mmcli_output)
    if match2:
        return match2.group(1).strip()
    return None
