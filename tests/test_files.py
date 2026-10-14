import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from prismos import files


class NativeFilesTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "Documents").mkdir()
        (self.root / "Hello.txt").write_text("hello")
        (self.root / ".hidden").write_text("hidden")

    def test_browse_sorted_folders_first_and_filters_hidden(self):
        data = files.browse(str(self.root))
        self.assertEqual([x["name"] for x in data["items"]], ["Documents","Hello.txt"])
        self.assertEqual(data["items"][1]["size"], "5 B")
        self.assertEqual(len(files.browse(str(self.root), True)["items"]), 3)

    def test_rejects_relative_or_control_path(self):
        for path in ("", "../folder", "a/b", "/tmp/\x00", "a"*4097):
            with self.subTest(path=path), self.assertRaises(ValueError):
                files.location(path)

    def test_filename_cannot_escape_parent(self):
        for name in ("", ".", "..", "../secret", "foo/bar", "space ", "bad\\name"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                files.filename(name)

    def test_create_folder_and_refuse_existing(self):
        path = files.create_folder(str(self.root), "New stuff")["path"]
        self.assertTrue(Path(path).is_dir())
        with self.assertRaises(FileExistsError):
            files.create_folder(str(self.root), "New stuff")

    def test_rename_refuses_overwrite(self):
        files.rename(str(self.root/"Hello.txt"),"New.txt")
        self.assertEqual((self.root/"New.txt").read_text(), "hello")
        (self.root/"Another.txt").write_text("keep")
        with self.assertRaises(ValueError):
            files.rename(str(self.root/"New.txt"),"Another.txt")
        self.assertEqual((self.root/"Another.txt").read_text(), "keep")

    @patch("prismos.files.subprocess.Popen")
    def test_open_uses_argv_and_xdg_mime(self, spawn):
        files.open_item(str(self.root/"Hello.txt"))
        self.assertEqual(spawn.call_args.args[0],
                         ["xdg-open", str(self.root/"Hello.txt")])

    def test_symlink_rename_never_renames_target(self):
        target = self.root / "Hello.txt"
        link = self.root / "shortcut"
        link.symlink_to(target)
        files.rename(str(link), "newshortcut")
        self.assertTrue(target.is_file())
        self.assertTrue((self.root / "newshortcut").is_symlink())

    @patch("prismos.files.shutil.which", return_value="/usr/bin/gio")
    @patch("prismos.files.subprocess.run")
    def test_trash_uses_gio_and_no_shell(self, invoke, which):
        invoke.return_value.returncode = 0
        files.trash(str(self.root/"Hello.txt"))
        self.assertEqual(invoke.call_args.args[0],
                         ["gio","trash","--",str(self.root/"Hello.txt")])

    @patch("prismos.files.shutil.which", return_value="/usr/bin/gio")
    @patch("prismos.files.subprocess.run")
    def test_cannot_trash_home(self, invoke, which):
        with patch("prismos.files.Path.home", return_value=self.root):
            with self.assertRaises(ValueError):
                files.trash(str(self.root))
        invoke.assert_not_called()


if __name__ == "__main__":
    unittest.main()
