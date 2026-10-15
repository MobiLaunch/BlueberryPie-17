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
