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


    @patch.dict(os.environ, {}, clear=False)
    def test_copy_paste_preserves_source_and_prevents_overwrite(self):
        with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(self.root)}):
            destination = self.root / "Documents"
            files.stage(str(self.root/"Hello.txt"), "copy")
            self.assertTrue(files.clipboard_status()["has_item"])
            files.paste(str(destination))
            self.assertEqual((destination/"Hello.txt").read_text(), "hello")
            self.assertTrue((self.root/"Hello.txt").exists())
            with self.assertRaises(ValueError):
                files.paste(str(destination))

    def test_cut_paste_moves_without_unintended_overwrite(self):
        with patch.dict(os.environ, {"XDG_RUNTIME_DIR": str(self.root)}):
            dest = self.root / "Documents"
            files.stage(str(self.root/"Hello.txt"), "cut")
            with patch("prismos.files.shutil.which", return_value="/usr/bin/gio"):
                import subprocess
                def simulated_gio(args, **kw):
                    source, target = args[-2:]
                    os.rename(source, target)
                    return type("Result", (), {"returncode": 0, "stderr": ""})()
                with patch("prismos.files.subprocess.run", side_effect=simulated_gio):
                    files.paste(str(dest))
            self.assertFalse((self.root/"Hello.txt").exists())
            self.assertTrue((dest/"Hello.txt").exists())
            self.assertFalse(files.clipboard_status()["has_item"])

    def test_nested_folder_copy_is_rejected(self):
        nested = self.root / "Documents" / "Child"
        nested.mkdir()
        with self.assertRaises(ValueError):
            files.transfer(str(self.root/"Documents"), str(nested))

    def test_symlink_copy_preserves_link_not_target_bytes(self):
        shortcut = self.root / "shortcut"
        shortcut.symlink_to(self.root / "Hello.txt")
        result = files.transfer(str(shortcut), str(self.root/"Documents"))
        self.assertTrue(Path(result["path"]).is_symlink())

    def test_cached_thumbnail_only_for_small_valid_images(self):
        from PIL import Image
        image = self.root / "sample.png"
        Image.new("RGB", (32, 32)).save(image)
        with patch.dict(os.environ, {"XDG_CACHE_HOME": str(self.root/"cache")}):
            first = files.browse(str(self.root))
            entry = next(item for item in first["items"] if item["name"] == "sample.png")
            self.assertTrue(entry["thumbnail"].startswith("file:///"))
            again = files.browse(str(self.root))
            second = next(item for item in again["items"] if item["name"] == "sample.png")
            self.assertEqual(entry["thumbnail"], second["thumbnail"])

    @patch("prismos.files.shutil.which", return_value="/usr/bin/gio")
    @patch("prismos.files.subprocess.run")
    def test_cannot_trash_home(self, invoke, which):
        with patch("prismos.files.Path.home", return_value=self.root):
            with self.assertRaises(ValueError):
                files.trash(str(self.root))
        invoke.assert_not_called()


if __name__ == "__main__":
    unittest.main()
