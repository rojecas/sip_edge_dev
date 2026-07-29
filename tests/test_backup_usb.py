"""Hardware-dependent tests for backup USB detection (EdgeBox only).
Requires a USB device physically connected and mounted."""

import os
import subprocess
import tempfile
import unittest
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models import BackupLog, Base


class TestBackupUsbOnEdgeBox(unittest.TestCase):
    """Verifies backup copies to a physically connected USB device.
    
    These tests run only on the EdgeBox (DEV_MODE=false) where a real USB
    is expected at /media/sipedge/GENIUS or similar mount point.
    """

    @classmethod
    def setUpClass(cls):
        # Required env vars for src/backup._mysqldump_to_file
        for k, v in {"DB_HOST": "localhost", "DB_PORT": "3306",
                      "DB_USER": "sip_user", "DB_PASSWORD": "sip_pass",
                      "DB_NAME": "sip_edge"}.items():
            if k not in os.environ:
                os.environ[k] = v

        cls.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.TestSessionLocal = sessionmaker(bind=cls.engine)

    def setUp(self):
        self._patcher = mock.patch(
            "src.database.SessionLocal", self.TestSessionLocal,
        )
        self._patcher.start()
        db = self.TestSessionLocal()
        db.query(BackupLog).delete()
        db.commit()
        db.close()

    def tearDown(self):
        self._patcher.stop()

    def test_backup_copies_to_connected_usb(self):
        """CUANDO hay un USB montado, el backup DEBE copiarse a el.

        find_removable_media() escanea /proc/mounts y detecta el medio.
        El backup se copia con CRC32 correcto y usb_copied=True.
        """
        from src.backup import find_removable_media, run_backup

        usb_path = find_removable_media()
        if not usb_path:
            self.skipTest("No USB device detected. Connect a USB drive.")

        with tempfile.TemporaryDirectory() as local:
            with mock.patch("src.backup.subprocess.Popen") as mock_popen:
                mock_proc = mock.MagicMock()
                mock_proc.returncode = 0
                mock_proc.communicate.return_value = (b"dump content", b"")
                mock_popen.return_value = mock_proc

                run_backup(usb_path, local, 30)

                self.assertTrue(
                    os.path.exists(usb_path),
                    f"USB mount point {usb_path} should exist",
                )

                db = self.TestSessionLocal()
                logs = db.query(BackupLog).all()
                db.close()
                self.assertEqual(len(logs), 1)
                self.assertTrue(logs[0].usb_copied,
                                "Backup must be copied to USB when device is present")
                self.assertIsNone(logs[0].error_message,
                                  "No error expected when USB copy succeeds")
