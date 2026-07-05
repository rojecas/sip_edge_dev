"""Cola de envio asincrona de SMS en thread separado.

Feature 27 ΓÇö sms_persistence.
Elimina el bloqueo del event loop de uvicorn y del watchdog de systemd.
"""

import logging
import os
import threading
import time as time_module

from src.sms_persistence import SmsPersistenceService

logger = logging.getLogger(__name__)


class SmsSendQueueError(Exception):
    """Error de la cola de envio asincrona."""
    pass


class SmsSendQueue:
    """Cola de envio de SMS en thread dedicado.

    Consume sms_messages con direction='sent' y status='pending',
    y ejecuta el envio fisico via mmcli sin bloquear el event loop
    de FastAPI.
    """

    MAX_RETRIES = 3

    def __init__(
        self,
        persistence: SmsPersistenceService,
        sms_service,
        modem_index: int,
        timeout_seconds: int = 20,
        poll_interval: float = 2.0,
        min_send_interval: float = 60.0,
    ) -> None:
        self._persistence = persistence
        self._sms_service = sms_service
        self._modem_index = modem_index
        self._timeout_seconds = timeout_seconds
        self._poll_interval = poll_interval
        self._min_send_interval = min_send_interval
        self._last_send_times: dict[str, float] = {}
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Inicia el thread de la cola de envio."""
        if self._running:
            logger.warning("SmsSendQueue: ya esta corriendo")
            return
        self._stop_event.clear()
        self._running = True
        self._thread = threading.Thread(
            target=self._worker_loop, daemon=True, name="sms-send-queue",
        )
        self._thread.start()
        logger.info(
            "SmsSendQueue: thread iniciado (timeout=%ss, poll=%ss)",
            self._timeout_seconds, self._poll_interval,
        )

    def stop(self) -> None:
        """Detiene el thread de la cola de envio."""
        if not self._running:
            return
        logger.info("SmsSendQueue: deteniendo thread...")
        self._stop_event.set()
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=10.0)
        logger.info("SmsSendQueue: thread detenido")

    def is_running(self) -> bool:
        """Retorna True si el thread esta corriendo."""
        return self._running and self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    # Worker
    # ------------------------------------------------------------------

    def _worker_loop(self) -> None:
        """Bucle principal del thread: polling de mensajes pendientes."""
        logger.info("SmsSendQueue: worker loop iniciado")
        while not self._stop_event.is_set():
            try:
                self._process_pending_messages()
            except Exception:
                logger.exception("SmsSendQueue: error en worker loop")
            self._stop_event.wait(timeout=self._poll_interval)
        logger.info("SmsSendQueue: worker loop terminado")

    def _process_pending_messages(self) -> None:
        """Procesa mensajes pendientes de envio.

        Recupera hasta 5 mensajes pendientes y los envia uno a uno.
        Cada mensaje tiene hasta MAX_RETRIES intentos.
        """
        try:
            pending = self._persistence.get_pending_outgoing_messages(limit=5)
        except Exception:
            logger.exception("SmsSendQueue: error consultando mensajes pendientes")
            return

        for msg in pending:
            if self._stop_event.is_set():
                break
            try:
                self._send_with_retry(msg)
            except Exception:
                logger.exception(
                    "SmsSendQueue: error procesando mensaje %s", msg.id,
                )

    def _send_with_retry(self, msg) -> bool:
        """Intenta enviar un mensaje con hasta MAX_RETRIES intentos.

        Args:
            msg: Instancia de SmsMessage con direction='sent'.

        Returns:
            True si el envio fue exitoso, False si fallo tras todos los intentos.
        """
        # B3: DRY_RUN - no enviar realmente
        dry_run = os.getenv("SMS_DRY_RUN", "false").lower() in ("true", "1", "yes")
        if dry_run:
            self._persistence.update_message_status(msg.id, "sent")
            logger.info(
                "[DRY_RUN] SendQueue salta mensaje %s a %s",
                msg.id, msg.peer_number,
            )
            return True

        now = time_module.time()
        last = self._last_send_times.get(msg.peer_number, 0.0)
        elapsed = now - last
        if elapsed < self._min_send_interval:
            self._stop_event.wait(timeout=self._min_send_interval - elapsed)
        self._last_send_times[msg.peer_number] = time_module.time()
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.debug(
                    "SmsSendQueue: enviando mensaje %s a %s (intento %d/%d)",
                    msg.id, msg.peer_number, attempt, self.MAX_RETRIES,
                )
                success = self._sms_service._send_via_mmcli_sync(
                    msg.peer_number, msg.body, message_id=msg.id,
                )
                if success:
                    self._persistence.update_message_status(msg.id, "sent")
                    logger.info(
                        "SmsSendQueue: mensaje %s enviado exitosamente (intento %d)",
                        msg.id, attempt,
                    )
                    return True
                else:
                    logger.warning(
                        "SmsSendQueue: intento %d/%d fallo para mensaje %s",
                        attempt, self.MAX_RETRIES, msg.id,
                    )
            except Exception as exc:
                logger.error(
                    "SmsSendQueue: excepcion en intento %d/%d para mensaje %s: %s",
                    attempt, self.MAX_RETRIES, msg.id, exc,
                )

            # Pequena pausa entre reintentos (backoff lineal)
            if attempt < self.MAX_RETRIES:
                self._stop_event.wait(timeout=1.0)

        # Todos los intentos fallaron
        self._persistence.update_message_status(
            msg.id, "failed",
            error_message=f"Failed after {self.MAX_RETRIES} retries",
        )
        logger.error(
            "SmsSendQueue: mensaje %s fallo tras %d intentos",
            msg.id, self.MAX_RETRIES,
        )
        return False
