"""Dispatcher v2 de SMS entrantes con persistencia antes de delegar.

Feature 27 — sms_persistence.
Persiste todos los SMS entrantes en sms_messages y crea conversaciones
automaticamente. Reemplaza a IncomingSmsDispatcher (v1).
"""

import asyncio
import logging
import re
import subprocess
from typing import Protocol, runtime_checkable

from src.sms_persistence import SmsPersistenceService

logger = logging.getLogger(__name__)

_SMS_ID_RE = re.compile(r"/org/freedesktop/ModemManager1/SMS/(\d+)")

# Numeros de carrier tipicos en Colombia: Tigo (369, 888, etc.)
# Cualquier numero con menos de 6 digitos se considera carrier
_MIN_PEER_DIGITS = 6


@runtime_checkable
class SmsHandler(Protocol):
    """Protocolo para handlers de SMS entrantes (compatible con v1).

    Cada handler recibe (sender_phone, text) y retorna True si el SMS fue
    procesado. Si un handler retorna True, los handlers siguientes no se
    ejecutan para ese SMS.
    """

    def __call__(self, sender_phone: str, text: str) -> bool:
        ...


class IncomingSmsDispatcherV2:
    """Dispatcher v2 de SMS entrantes con persistencia.

    Ejecuta un unico bucle asyncio que consulta mmcli cada 15 segundos
    y distribuye los SMS a los handlers registrados con workflow_type.
    En modo desarrollo, consume de una cola interna.

    Diferencias con v1:
    - Persiste el SMS en sms_messages ANTES de delegar.
    - Crea conversacion si no existe.
    - No tiene handler catch-all: SMS no manejados reciben ayuda.
    - SMS de carrier se persisten sin respuesta.
    """

    HELP_RESPONSE = (
        "Comando no reconocido. Comandos validos: "
        "manual on, manual off, reset password <usuario>"
    )

    def __init__(
        self,
        modem_index: int,
        dev_mode: bool,
        persistence: SmsPersistenceService,
    ) -> None:
        self._modem_index = modem_index
        self._dev_mode = dev_mode
        self._persistence = persistence
        self._handlers: list[tuple[SmsHandler, str]] = []  # (handler, workflow_type)
        self._dev_queue: list[tuple[str, str, str | None]] = []
        self._poll_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Registro de handlers
    # ------------------------------------------------------------------

    def register_handler(
        self, handler: SmsHandler, workflow_type: str,
    ) -> None:
        """Registra un handler de SMS con su workflow_type.

        Args:
            handler: Funcion que procesa el SMS (sender_phone, text) -> bool.
            workflow_type: Tipo de workflow asociado (ej. 'emergency').
        """
        self._handlers.append((handler, workflow_type))
        logger.debug(
            "DispatcherV2: handler %s registrado con workflow_type=%s",
            handler, workflow_type,
        )

    def enqueue_incoming_sms(
        self, sender_phone: str, text: str, modem_sms_id: str | None = None,
    ) -> None:
        """Encola un SMS entrante simulado (para dev mode y tests)."""
        self._dev_queue.append((sender_phone, text, modem_sms_id))

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Inicia el bucle de polling asyncio."""
        if self._poll_task is not None and not self._poll_task.done():
            logger.warning("DispatcherV2: polling ya esta corriendo")
            return
        logger.info("DispatcherV2: iniciando polling de SMS")
        self._poll_task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Cancela el bucle de polling."""
        if self._poll_task is not None and not self._poll_task.done():
            logger.info("DispatcherV2: deteniendo polling de SMS")
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
                logger.info("DispatcherV2: polling cancelado")
                break
            except Exception:
                logger.exception("DispatcherV2: error en polling de SMS entrantes")
            try:
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                logger.info("DispatcherV2: polling cancelado durante sleep")
                break

    async def _check_incoming_sms(self) -> None:
        """Verifica si hay SMS entrantes y los distribuye a los handlers."""
        messages: list[tuple[str, str, str | None]] = []

        if self._dev_mode:
            while self._dev_queue:
                sender, text, sms_id = self._dev_queue.pop(0)
                messages.append((sender, text, sms_id))
        else:
            mmcli_msgs = await self._fetch_mmcli_sms()
            messages.extend(mmcli_msgs)

        for sender_phone, text, modem_sms_id in messages:
            await asyncio.to_thread(
                self._dispatch, sender_phone, text, modem_sms_id,
            )

    async def _fetch_mmcli_sms(self) -> list[tuple[str, str, str | None]]:
        """Consulta mmcli para listar y leer SMS entrantes."""
        messages: list[tuple[str, str, str | None]] = []
        try:
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
                        await self._delete_sms(sms_id)
                        continue

                    status = _extract_sms_field(read.stdout, "state")
                    # B2: Si no se puede determinar el estado O no es "received",
                    # eliminar y saltar para evitar loops con SMS huerfanos
                    if not status or status.lower() != "received":
                        await self._delete_sms(sms_id)
                        continue

                    sender = _extract_sms_field(read.stdout, "number")
                    text = _extract_sms_field(read.stdout, "text")

                    # Fix 3: Si el modem_sms_id existe en BD, es un SMS que nosotros
                    # creamos al enviar. Eliminarlo y saltar para evitar loop.
                    if sender and text:
                        try:
                            sms_modem_id = int(sms_id)
                            if self._persistence.message_exists_by_modem_id(sms_modem_id):
                                logger.info(
                                    "DispatcherV2: SMS %s es auto-generado "
                                    "(modem_id=%s), eliminando",
                                    sms_id, sms_modem_id,
                                )
                                await self._delete_sms(sms_id)
                                continue
                        except Exception:
                            pass  # Si falla la consulta, procesar normalmente

                    if sender and text:
                        messages.append((sender, text, sms_id))

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
                [
                    "sudo", "-n", "mmcli", "-m", str(self._modem_index),
                    f"--messaging-delete-sms={sms_id}",
                ],
                capture_output=True,
                timeout=10,
            )
        except Exception:
            logger.warning("Failed to delete SMS id=%s", sms_id)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _dispatch(
        self, sender_phone: str, text: str, modem_sms_id: str | None = None,
    ) -> None:
        """Distribuye un SMS a los handlers registrados.

        Flujo:
        1. Si es SMS de carrier (< 6 digitos): persistir unknown, no responder.
        2. Persistir el SMS entrante en sms_messages con status='received'.
        3. Crear conversacion si no existe (workflow_type inicial 'unknown').
        4. Delegar a handlers registrados en orden.
        5. Si ningun handler retorna True: responder con ayuda y marcar unknown.
        """
        trimmed_text = text.strip()

        # R7: SMS de carrier (numeros cortos)
        if self._is_carrier_number(sender_phone):
            self._handle_carrier_sms(sender_phone, trimmed_text)
            return

        # R3: Persistir SMS entrante ANTES de delegar
        # R4: Crear conversacion si no existe
        try:
            # Inicialmente workflow_type='unknown' — los handlers lo pueden cambiar
            conv = self._persistence.get_or_create_active_conversation(
                peer_number=sender_phone, workflow_type="unknown",
            )
            msg = self._persistence.create_message(
                conversation_id=conv.id,
                direction="received",
                peer_number=sender_phone,
                body=trimmed_text,
                handler=None,
                status="received",
                modem_sms_id=int(modem_sms_id) if modem_sms_id is not None else None,
            )
        except Exception:
            logger.exception(
                "DispatcherV2: error persistiendo SMS entrante de %s", sender_phone,
            )
            return

        # R3 cumplido: el SMS ya esta en BD. Ahora delegar.
        handled = False
        for handler, workflow_type in self._handlers:
            try:
                if handler(sender_phone, trimmed_text):
                    handled = True
                    logger.debug(
                        "DispatcherV2: SMS manejado por %s (workflow=%s)",
                        handler, workflow_type,
                    )
                    break
            except Exception:
                logger.exception(
                    "DispatcherV2: handler %s fallo procesando SMS", handler,
                )

        # R6: Si ningun handler retorno True, responder con ayuda
        if not handled:
            logger.info(
                "DispatcherV2: SMS no manejado de %s: '%s'", sender_phone, trimmed_text,
            )
            # Marcar conversacion como unknown/completed
            self._persistence.update_conversation_status(conv.id, "completed")
            # Enviar respuesta de ayuda (persistiendo el mensaje de respuesta)
            self._persistence.create_message(
                conversation_id=conv.id,
                direction="sent",
                peer_number=sender_phone,
                body=self.HELP_RESPONSE,
                handler="dispatcher_v2",
                status="pending",
            )

    # ------------------------------------------------------------------
    # Carrier SMS (R7)
    # ------------------------------------------------------------------

    def _is_carrier_number(self, phone: str) -> bool:
        """Determina si un numero es de carrier (corto, < 6 digitos)."""
        # Extraer solo digitos
        digits = re.sub(r"\D", "", phone)
        return len(digits) < _MIN_PEER_DIGITS

    def _handle_carrier_sms(self, sender_phone: str, text: str) -> None:
        """Persiste SMS de carrier como unknown/completed sin responder (R7)."""
        try:
            conv = self._persistence.create_conversation(
                peer_number=sender_phone,
                workflow_type="unknown",
                status="completed",
            )
            self._persistence.create_message(
                conversation_id=conv.id,
                direction="received",
                peer_number=sender_phone,
                body=text,
                handler="carrier",
                status="received",
            )
            logger.info(
                "DispatcherV2: SMS de carrier %s persistido sin respuesta", sender_phone,
            )
        except Exception:
            logger.exception(
                "DispatcherV2: error persistiendo SMS de carrier %s", sender_phone,
            )


def _extract_sms_field(mmcli_output: str, field: str) -> str | None:
    """Extrae el valor de un campo de la salida de mmcli -s <id>."""
    pattern = re.compile(
        r"\|\s*" + re.escape(field) + r"\s*:\s*(.+)$",
        re.MULTILINE,
    )
    match = pattern.search(mmcli_output)
    if match:
        return match.group(1).strip()
    return None
