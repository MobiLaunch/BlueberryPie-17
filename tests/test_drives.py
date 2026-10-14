import json
import unittest
from unittest.mock import patch

from prismos import drives


class RemovableDrivesTests(unittest.TestCase):
    @patch("prismos.drives.shutil.which", return_value="/usr/bin/udisksctl")
    @patch("prismos.drives.run")
    def test_only_removable_volumes_shown(self, run, which):
        run.return_value = json.dumps({"blockdevices": [
            {"path":"/dev/nvme0n1","type":"disk","rm":False,"tran":"nvme",
             "children":[{"path":"/dev/nvme0n1p1","type":"part",
                          "fstype":"ext4","mountpoint":"/"}]},
            {"path":"/dev/sdb","type":"disk","rm":False,"tran":"usb",
             "children":[{"path":"/dev/sdb1","type":"part","fstype":"vfat",
                          "label":"Backup","mountpoint":"/run/media/USB"}]}
        ]})
        found = drives.volumes()["items"]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["device"], "/dev/sdb1")
        self.assertTrue(found[0]["mounted"])

    @patch("prismos.drives.run")
    def test_cannot_change_internal_volume(self, run):
        with patch("prismos.drives.volumes", return_value={
                "items":[{"device":"/dev/sdb1","mounted":True}]}):
            with self.assertRaises(ValueError):
                drives.change("unmount", "/dev/nvme0n1p1")
        run.assert_not_called()

    @patch("prismos.drives.shutil.which", return_value="/usr/bin/udisksctl")
    @patch("prismos.drives.run", return_value="Unmounted /dev/sdb1")
    @patch("prismos.drives.volumes")
    def test_unmount_is_polkit_guarded(self, volumes, run, which):
        volumes.return_value = {"items":[{"device":"/dev/sdb1","mounted":True}]}
        drives.change("unmount", "/dev/sdb1")
        run.assert_called_once_with(
            ["udisksctl","unmount","--block-device","/dev/sdb1"], timeout=90)

    def test_injection_rejected_before_commands(self):
        for path in ("/dev/sdb1;reboot", "../../etc/passwd", "--help", "/dev/sd a"):
            with self.assertRaises(ValueError):
                drives.change("mount", path)


if __name__ == "__main__":
    unittest.main()
