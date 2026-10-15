import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from prismos import cli, clipboard, settings
from prismos.system import CommandError

LISTING = "12\thello world\n11\t[[ binary data 14 KiB png 800x600 ]]\n10\tline\twith tab\nbad\tskipped\n9\t" + "x" * 300


class Isolated(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name, "XDG_RUNTIME_DIR": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        which = patch("prismos.clipboard.shutil.which", side_effect=lambda name: "/usr/bin/" + name)
        which.start()
        self.addCleanup(which.stop)

    def call(self, argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(argv)
        return code, json.loads(out.getvalue())


class HistoryTests(Isolated):
    @patch("prismos.clipboard.run", return_value=LISTING)
    def test_history_is_empty_until_enabled(self, run):
        self.assertEqual(self.call(["clipboard", "list"])[1]["items"], [])
        run.assert_not_called()

    @patch("prismos.clipboard.run", return_value=LISTING)
    def test_entries_are_parsed_and_bounded(self, run):
        settings.update(clipboard_history=True)
        items = self.call(["clipboard", "list"])[1]["items"]
        self.assertEqual([item["id"] for item in items], ["12", "11", "10", "9"])
        self.assertEqual(items[1], {"id": "11", "kind": "image", "preview": "Image"})
        self.assertEqual(items[2]["preview"], "line with tab")
        self.assertEqual(len(items[3]["preview"]), 120)

    def test_unavailable_tools_report_cleanly(self):
        with patch("prismos.clipboard.shutil.which", return_value=None):
            result = self.call(["clipboard", "list"])[1]
            self.assertFalse(result["available"])
            code, error = self.call(["clipboard", "enable"])
            self.assertEqual(code, 1)
            self.assertFalse(settings.load()["clipboard_history"])


class ActionTests(Isolated):
    def test_ids_are_digits_only(self):
        for bad in ("1;reboot", "../1", "", "-1", "1 2", "a"):
            code, result = self.call(["clipboard", "copy", bad]) if bad else (1, {})
            self.assertEqual(code, 1, bad)
        self.assertEqual(self.call(["clipboard", "delete", "x"])[0], 1)

    @patch("prismos.clipboard.subprocess.run", return_value=MagicMock(returncode=0))
    @patch("prismos.clipboard.subprocess.Popen")
    def test_copy_pipes_decode_into_wl_copy_without_a_shell(self, popen, run):
        decoder = popen.return_value
        decoder.returncode = 0
        clipboard.copy("42")
        self.assertEqual(popen.call_args.args[0], ["cliphist", "decode", "42"])
        self.assertEqual(run.call_args.args[0], ["wl-copy"])
        self.assertIs(run.call_args.kwargs["stdin"], decoder.stdout)

    @patch("prismos.clipboard.subprocess.run", return_value=MagicMock(returncode=1))
    @patch("prismos.clipboard.subprocess.Popen")
    def test_failed_copy_is_an_error(self, popen, run):
        popen.return_value.returncode = 0
        with self.assertRaises(CommandError):
            clipboard.copy("42")

    @patch("prismos.clipboard.subprocess.run")
    @patch("prismos.clipboard.run", return_value=LISTING)
    def test_delete_sends_the_original_line_on_stdin(self, run, sub):
        settings.update(clipboard_history=True)
        clipboard.delete("12")
        self.assertEqual(sub.call_args.args[0], ["cliphist", "delete"])
        self.assertEqual(sub.call_args.kwargs["input"], b"12\thello world")
        with self.assertRaises(ValueError):
            clipboard.delete("999")

    @patch("prismos.clipboard.run", return_value="")
    def test_clear_wipes(self, run):
        clipboard.clear()
        run.assert_called_with(["cliphist", "wipe"], timeout=6)


class PinTests(Isolated):
    def setUp(self):
        super().setUp()
        patcher = patch.dict(os.environ, {"XDG_DATA_HOME": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        settings.update(clipboard_history=True)

    def run_for(self, decoded):
        def fake(argv, timeout=4):
            return LISTING if argv[:2] == ["cliphist", "list"] else decoded
        return patch("prismos.clipboard.run", side_effect=fake)

    def test_pin_copies_the_text_into_a_private_file_and_survives_clearing(self):
        with self.run_for("hello world"):
            result = self.call(["clipboard", "pin", "12"])[1]
        self.assertEqual(result["pins"], [{"id": 1, "preview": "hello world"}])
        from stat import S_IMODE
        self.assertEqual(S_IMODE(clipboard.pins_path().stat().st_mode), 0o600)
        with patch("prismos.clipboard.run", return_value=""):
            clipboard.clear()
        self.assertEqual(clipboard.status(items=False)["pins"][0]["id"], 1)

    def test_duplicates_images_and_oversize_entries_are_not_pinned(self):
        with self.run_for("hello world"):
            self.call(["clipboard", "pin", "12"])
            self.call(["clipboard", "pin", "12"])
            self.assertEqual(len(clipboard.load_pins()), 1)
            self.assertEqual(self.call(["clipboard", "pin", "11"])[0], 1)      # image
            self.assertEqual(self.call(["clipboard", "pin", "999"])[0], 1)     # gone
        with self.run_for("x" * (clipboard.PIN_MAX + 1)):
            self.assertEqual(self.call(["clipboard", "pin", "10"])[0], 1)

    def test_limit_and_unpin(self):
        clipboard.save_pins([{"id": n, "text": f"t{n}"} for n in range(1, clipboard.PIN_LIMIT + 1)])
        with self.run_for("brand new"):
            self.assertEqual(self.call(["clipboard", "pin", "12"])[0], 1)
        self.assertEqual(len(self.call(["clipboard", "unpin", "3"])[1]["pins"]), clipboard.PIN_LIMIT - 1)
        for bad in ("x", "-1", "1;2"):
            self.assertEqual(self.call(["clipboard", "unpin", bad])[0], 1, bad)

    @patch("prismos.clipboard.subprocess.run", return_value=MagicMock(returncode=0))
    def test_copy_pin_sends_the_text_on_stdin_to_wl_copy(self, run):
        clipboard.save_pins([{"id": 4, "text": "line1\nline2"}])
        self.call(["clipboard", "copy-pin", "4"])
        self.assertEqual(run.call_args.args[0], ["wl-copy"])
        self.assertEqual(run.call_args.kwargs["input"], b"line1\nline2")
        self.assertEqual(self.call(["clipboard", "copy-pin", "9"])[0], 1)

    def test_corrupt_pin_files_are_filtered(self):
        clipboard.pins_path().parent.mkdir(parents=True, exist_ok=True)
        clipboard.pins_path().write_text(json.dumps([{"id": 1, "text": "ok"}, {"id": "2", "text": "bad"}, {"id": 3, "text": ""},
                                                     "junk", {"id": 4, "text": "x" * 5000}]))
        self.assertEqual(clipboard.load_pins(), [{"id": 1, "text": "ok"}])
        clipboard.pins_path().write_text("not json")
        self.assertEqual(clipboard.load_pins(), [])

    def test_pins_are_listed_even_when_history_is_off(self):
        settings.update(clipboard_history=False)
        clipboard.save_pins([{"id": 1, "text": "keep me"}])
        self.assertEqual(self.call(["clipboard", "list"])[1]["pins"], [{"id": 1, "preview": "keep me"}])


class WatcherTests(Isolated):
    @patch("prismos.clipboard.entries", return_value=[])
    @patch("prismos.clipboard._alive", return_value=False)
    @patch("prismos.clipboard.subprocess.Popen")
    def test_enable_starts_two_watchers_and_remembers_them(self, popen, alive, entries):
        popen.side_effect = [MagicMock(pid=101), MagicMock(pid=102)]
        clipboard.enable(True)
        self.assertEqual([call.args[0][:4] for call in popen.call_args_list],
                         [["wl-paste", "--type", "text", "--watch"], ["wl-paste", "--type", "image", "--watch"]])
        self.assertTrue(settings.load()["clipboard_history"])
        self.assertEqual(json.loads(clipboard.state_file().read_text()), [101, 102])

    @patch("prismos.clipboard.os.kill")
    @patch("prismos.clipboard._alive", side_effect=lambda pid: pid != 103)
    def test_disable_stops_only_verified_watchers(self, alive, kill):
        clipboard.state_file().write_text(json.dumps([101, 103, "x"]))
        settings.update(clipboard_history=True)
        clipboard.enable(False)
        kill.assert_called_once_with(101, 15)
        self.assertFalse(settings.load()["clipboard_history"])
        self.assertFalse(clipboard.state_file().exists())

    def test_alive_checks_the_process_name(self):
        self.assertFalse(clipboard._alive(os.getpid()))
        self.assertFalse(clipboard._alive("x"))
        self.assertFalse(clipboard._alive(99999999))

    @patch("prismos.clipboard.subprocess.Popen")
    def test_resume_does_nothing_unless_enabled(self, popen):
        clipboard.resume()
        popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
