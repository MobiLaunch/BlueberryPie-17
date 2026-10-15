import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from prismos import cli, emoji, settings
from prismos.system import CommandError

GOOD = ["😀", "👍️", "❤️‍🔥", "🇨🇦", "1️⃣", "#️⃣", "*⃣", "👨‍👩‍👧‍👦", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "©️", "✔️"]
BAD = ["", "a", "hello", "😀 ", "\n", "😀\n", "1", "#", "; rm -rf /", "$(reboot)", "😀" * 17, "é", "-", "\x1b[0m", None, 5]


class EmojiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_only_emoji_like_text_is_accepted(self):
        for text in GOOD:
            self.assertTrue(emoji.valid(text), repr(text))
        for text in BAD:
            self.assertFalse(emoji.valid(text), repr(text))

    def test_every_emoji_the_picker_offers_is_accepted(self):
        import re
        from pathlib import Path
        source = (Path(__file__).resolve().parent.parent / "shell/services/EmojiData.js").read_text()
        entries = json.loads(re.search(r"var entries = (\[.*\]);", source, re.S).group(1))
        self.assertGreater(len(entries), 1800)
        rejected = [entry[0] for entry in entries if not emoji.valid(entry[0])]
        self.assertEqual(rejected, [])

    def test_copy_pipes_the_text_to_wl_copy_and_remembers_it(self):
        with patch("prismos.emoji.shutil.which", return_value="/usr/bin/wl-copy"), \
                patch("prismos.emoji.subprocess.run") as run:
            run.return_value.returncode = 0
            for text in ("😀", "👍️", "😀"):
                self.assertEqual(emoji.copy(text), {"ok": True, "copied": text})
        self.assertEqual(run.call_args.args[0], ["wl-copy"])
        self.assertEqual(run.call_args.kwargs["input"], "😀".encode())
        self.assertEqual(settings.load()["recent_emoji"], ["😀", "👍️"], "newest first, no duplicates")

    def test_recents_are_capped(self):
        with patch("prismos.emoji.shutil.which", return_value="/x/wl-copy"), patch("prismos.emoji.subprocess.run") as run:
            run.return_value.returncode = 0
            for code in range(0x1F600, 0x1F600 + 40):
                emoji.copy(chr(code))
        recent = settings.load()["recent_emoji"]
        self.assertEqual((len(recent), recent[0]), (emoji.MAX_RECENT, chr(0x1F600 + 39)))

    def test_bad_text_never_reaches_the_clipboard_or_settings(self):
        with patch("prismos.emoji.subprocess.run") as run:
            for text in BAD:
                with self.subTest(text=text), self.assertRaises(ValueError):
                    emoji.copy(text)
        run.assert_not_called()
        self.assertEqual(settings.load()["recent_emoji"], [])

    def test_failures_are_reported(self):
        with patch("prismos.emoji.shutil.which", return_value=None), self.assertRaises(CommandError):
            emoji.copy("😀")
        with patch("prismos.emoji.shutil.which", return_value="/x/wl-copy"), patch("prismos.emoji.subprocess.run") as run:
            run.return_value.returncode = 1
            with self.assertRaises(CommandError):
                emoji.copy("😀")
        self.assertEqual(settings.load()["recent_emoji"], [])

    def test_a_tampered_settings_file_is_cleaned_on_load(self):
        settings.directory().mkdir(parents=True)
        (settings.directory() / "settings.json").write_text(json.dumps(
            {"recent_emoji": ["😀", "rm -rf /", 3, "😀", "👍️"] + ["😀"] * 3}))
        self.assertEqual(settings.load()["recent_emoji"], ["😀", "👍️"])

    def test_cli(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["emoji", "recent"]), 0)
        self.assertEqual(json.loads(out.getvalue()), {"ok": True, "recent": []})
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(cli.main(["emoji", "copy", "hello"]), 1)
        self.assertFalse(json.loads(out.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
