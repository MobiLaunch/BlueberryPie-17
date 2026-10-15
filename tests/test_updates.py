import contextlib
import io
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prismos import cli, updates
from prismos.system import CommandError

PACMAN = """linux 6.18.1.arch1-1 -> 6.18.2.arch1-1
firefox 140.0-1 -> 141.0-1
evil;name 1 -> 2
broken line here
ttf-roboto 2.138-1 -> 2.138-2
"""
FLATPAK = "org.gnome.Calculator\nnot an id\norg.mozilla.firefox\textra\n"


def done(code, out="", err=""):
    return subprocess.CompletedProcess([], code, out, err)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CACHE_HOME": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.tools = {"checkupdates", "flatpak", "foot"}
        self.replies = {"checkupdates": done(0, PACMAN), "flatpak": done(0, FLATPAK)}
        self.calls = []
        for target, value in (("prismos.updates.shutil.which", lambda name: "/usr/bin/" + name if name in self.tools else None),
                              ("prismos.updates.subprocess.run", self.fake_run)):
            started = patch(target, side_effect=value)
            started.start()
            self.addCleanup(started.stop)

    def fake_run(self, args, **kwargs):
        self.calls.append(args)
        reply = self.replies[args[0]]
        if isinstance(reply, Exception):
            raise reply
        return reply

    def test_parses_only_well_formed_lines_and_sorts_them(self):
        result = updates.check()
        self.assertEqual([item["name"] for item in result["pacman"]["items"]], ["firefox", "linux", "ttf-roboto"])
        self.assertEqual(result["pacman"]["items"][1], {"name": "linux", "old": "6.18.1.arch1-1", "new": "6.18.2.arch1-1"})
        self.assertEqual([item["name"] for item in result["flatpak"]["items"]], ["org.gnome.Calculator", "org.mozilla.firefox"])
        self.assertEqual(result["total"], 5)

    def test_no_updates_is_exit_code_two_and_not_an_error(self):
        self.replies["checkupdates"] = done(2)
        self.replies["flatpak"] = done(0, "")
        result = updates.check()
        self.assertEqual((result["total"], result["pacman"]["error"], result["flatpak"]["error"]), (0, "", ""))

    def test_errors_and_timeouts_are_reported_per_source(self):
        self.replies["checkupdates"] = done(1, "", "error: failed to synchronize any databases")
        self.replies["flatpak"] = subprocess.TimeoutExpired("flatpak", 60)
        result = updates.check()
        self.assertIn("synchronize", result["pacman"]["error"])
        self.assertIn("did not finish", result["flatpak"]["error"])
        self.assertEqual(result["total"], 0)

    def test_missing_tools_are_explained_and_both_missing_is_an_error(self):
        self.tools = {"flatpak"}
        result = updates.check()
        self.assertFalse(result["pacman"]["available"])
        self.assertIn("pacman-contrib", result["pacman"]["error"])
        self.tools = set()
        with self.assertRaises(CommandError):
            updates.check()

    def test_checking_only_runs_read_only_commands(self):
        updates.check()
        self.assertEqual(self.calls, [["checkupdates"], ["flatpak", "remote-ls", "--updates", "--columns=application"]])

    def test_the_last_result_is_cached_privately_and_a_corrupt_cache_is_ignored(self):
        self.assertEqual((updates.cached()["checked"], updates.cached()["total"]), (0, 0))
        updates.check()
        path = updates.cache_path()
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
        again = updates.cached()
        self.assertEqual(again["total"], 5)
        self.assertGreater(again["checked"], 0)
        path.write_text(json.dumps({"checked": 5, "pacman": {"items": [
            {"name": "ok-pkg", "old": "1", "new": "2"}, {"name": "bad name;rm"}, 7]}, "flatpak": "nope"}))
        cleaned = updates.cached()
        self.assertEqual([item["name"] for item in cleaned["pacman"]["items"]], ["ok-pkg"])
        path.write_text("{not json")
        self.assertEqual(updates.cached()["total"], 0)

    def test_installing_opens_the_terminal_on_a_fixed_command_only(self):
        with patch("prismos.updates.subprocess.Popen") as popen:
            updates.apply("pacman")
            updates.apply("all")
        first, second = (call.args[0] for call in popen.call_args_list)
        self.assertEqual(first[:5], ["foot", "--title", "PrismOS update", "bash", "-c"])
        self.assertTrue(first[5].startswith("sudo pacman -Syu; echo"))
        self.assertTrue(second[5].startswith("sudo pacman -Syu; flatpak update; echo"))
        for bad in ("pacman; reboot", "", None, "ALL"):
            with self.subTest(kind=bad), self.assertRaises(ValueError):
                updates.apply(bad)
        self.tools.discard("foot")
        with self.assertRaises(CommandError):
            updates.apply("pacman")

    def test_cli_returns_json(self):
        for argv, key in ((["updates", "list"], "total"), (["updates", "check"], "pacman")):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cli.main(argv), 0)
            self.assertIn(key, json.loads(out.getvalue()))
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["updates", "apply", "nope"]), 1)
        self.assertFalse(json.loads(out.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
