content = r"""

class TestFindRemovableMedia(unittest.TestCase):
    def _make_mounts_file(self, tmpdir, lines):
        path = os.path.join(tmpdir, "mounts")
        with open(path, "w") as f:
            f.writelines(lines)
        return path

    def test_detects_first_usb_under_media(self):
        from src.backup import find_removable_media
        with tempfile.TemporaryDirectory() as d:
            mp = os.path.join(d, "media", "sipedge", "GENIUS")
            os.makedirs(mp)
            mounts = self._make_mounts_file(d, [
                "/dev/sda1 /boot vfat rw 0 0\n",
                f"/dev/sdb1 {mp} vfat rw,nosuid 0 0\n",
                "devpts /dev/pts devpts rw 0 0\n",
            ])
            with unittest.mock.patch("os.path.ismount", return_value=True):
                with unittest.mock.patch("os.access", return_value=True):
                    result = find_removable_media(mounts)
                    self.assertEqual(result, mp)

    def test_skips_non_media_mounts(self):
        from src.backup import find_removable_media
        with tempfile.TemporaryDirectory() as d:
            mounts = self._make_mounts_file(d, [
                "/dev/sda1 /boot ext4 rw 0 0\n",
                "/dev/sdb1 /mnt/usb vfat rw 0 0\n",
            ])
            with unittest.mock.patch("os.path.ismount", return_value=True):
                with unittest.mock.patch("os.access", return_value=True):
                    result = find_removable_media(mounts)
                    self.assertIsNone(result)

    def test_skips_non_writable(self):
        from src.backup import find_removable_media
        with tempfile.TemporaryDirectory() as d:
            mp = os.path.join(d, "media", "sipedge", "RO")
            os.makedirs(mp)
            mounts = self._make_mounts_file(d, [
                f"/dev/sdc1 {mp} vfat ro 0 0\n",
            ])
            with unittest.mock.patch("os.path.ismount", return_value=True):
                with unittest.mock.patch("os.access", return_value=False):
                    result = find_removable_media(mounts)
                    self.assertIsNone(result)

    def test_detects_mmcblk_sd_cards(self):
        from src.backup import find_removable_media
        with tempfile.TemporaryDirectory() as d:
            mp = os.path.join(d, "media", "sipedge", "SDCARD")
            os.makedirs(mp)
            mounts = self._make_mounts_file(d, [
                f"/dev/mmcblk0p1 {mp} vfat rw 0 0\n",
            ])
            with unittest.mock.patch("os.path.ismount", return_value=True):
                with unittest.mock.patch("os.access", return_value=True):
                    result = find_removable_media(mounts)
                    self.assertEqual(result, mp)

    def test_returns_none_when_no_mounts_file(self):
        from src.backup import find_removable_media
        with tempfile.TemporaryDirectory() as d:
            fake = os.path.join(d, "nonexistent")
            result = find_removable_media(fake)
            self.assertIsNone(result)

    def test_detects_run_media(self):
        from src.backup import find_removable_media
        with tempfile.TemporaryDirectory() as d:
            mp = os.path.join(d, "run", "media", "sipedge", "DISK")
            os.makedirs(mp)
            mounts = self._make_mounts_file(d, [
                f"/dev/sdd1 {mp} vfat rw 0 0\n",
            ])
            with unittest.mock.patch("os.path.ismount", return_value=True):
                with unittest.mock.patch("os.access", return_value=True):
                    result = find_removable_media(mounts)
                    self.assertEqual(result, mp)


class TestDetermineUsbPath(unittest.TestCase):
    def test_configured_path_takes_priority(self):
        from src.backup import _determine_usb_path
        with tempfile.TemporaryDirectory() as d:
            configured = os.path.join(d, "configured_usb")
            os.makedirs(configured)
            with unittest.mock.patch("src.backup.find_removable_media") as mock_find:
                mock_find.return_value = "/media/sipedge/GENIUS"
                result = _determine_usb_path(configured)
                self.assertEqual(result, configured)
                mock_find.assert_not_called()

    def test_configured_path_not_found_falls_back(self):
        from src.backup import _determine_usb_path
        with unittest.mock.patch("src.backup.find_removable_media") as mock_find:
            mock_find.return_value = "/media/sipedge/GENIUS"
            result = _determine_usb_path("/nonexistent/path")
            self.assertEqual(result, "/media/sipedge/GENIUS")
            mock_find.assert_called_once()

    def test_none_available_returns_none(self):
        from src.backup import _determine_usb_path
        with unittest.mock.patch("src.backup.find_removable_media") as mock_find:
            mock_find.return_value = None
            result = _determine_usb_path("/nonexistent/path")
            self.assertIsNone(result)
            mock_find.assert_called_once()
"""

with open(r'C:\MySource\sip_edge\tests\test_backup.py', 'a', encoding='utf-8') as f:
    f.write(content)

print('Done')
