"""Pure Python implementation of the sd_notify protocol for systemd watchdog.

Reads $NOTIFY_SOCKET and sends WATCHDOG=1 datagrams to notify systemd
that the service is still alive. Pure stdlib -- no external dependencies.

Usage:
    from src.sd_notify import notify
    notify()  # Sends WATCHDOG=1 if NOTIFY_SOCKET is set, no-op otherwise.
"""

import logging
import os
import socket

logger = logging.getLogger(__name__)


def notify() -> bool:
    """Send WATCHDOG=1 notification to systemd via $NOTIFY_SOCKET.

    Returns:
        True if the notification was sent successfully, False otherwise
        (e.g., $NOTIFY_SOCKET not set, socket error, etc.).

    This function NEVER raises an exception. All errors are logged and
    silently swallowed for graceful degradation.
    """
    notify_socket = os.environ.get("NOTIFY_SOCKET")
    if not notify_socket:
        return False

    # systemd $NOTIFY_SOCKET can start with "@" which means an abstract
    # Linux socket (instead of a filesystem path). Replace "@" with "\0".
    if notify_socket.startswith("@"):
        notify_socket = "\0" + notify_socket[1:]

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            sock.connect(notify_socket)
            sock.sendall(b"WATCHDOG=1\n")
            return True
        finally:
            sock.close()
    except OSError as e:
        logger.debug("sd_notify failed: %s", e)
        return False
