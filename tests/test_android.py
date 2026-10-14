import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from prismos import android, cli, settings
from prismos.system import CommandError


class AndroidOptInTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_android_off_and_onboarding_not_complete_by_default(self):
        self.assertFalse(settings.load()["android_enabled"])
        self.assertFalse(settings.load()["onboarding_complete"])

    def test_onboarding_no_never_enables_android(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(cli.main(["welcome", "finish", "--android", "no"]), 0)
        self.assertTrue(settings.load()["onboarding_complete"])
        self.assertFalse(settings.load()["android_enabled"])

    def test_onboarding_yes_preserves_opt_in(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["welcome", "finish", "--android", "yes"]), 0)
        self.assertTrue(settings.load()["android_enabled"])
        self.assertTrue(settings.load()["onboarding_complete"])

    def test_invalid_preference_types_are_ignored(self):
        settings.directory().mkdir()
        (settings.directory() / "settings.json").write_text(
            '{"android_enabled": "yes", "onboarding_complete": 1}')
        self.assertFalse(settings.load()["android_enabled"])
        self.assertFalse(settings.load()["onboarding_complete"])

    @patch("prismos.android.shutil.which", return_value=None)
    def test_missing_waydroid_gives_safe_off_status(self, which):
        state = android.status()
        self.assertFalse(state["available"])
        self.assertFalse(state["ready"])

    @patch("prismos.android.privileged_setup")
    @patch("prismos.android.subprocess.Popen")
    @patch("prismos.android.run", return_value="")
    @patch("prismos.android.status")
    @patch("prismos.android.shutil.which", return_value="/usr/bin/waydroid")
    def test_first_enable_reports_real_stages(self, which, state, run, popen, privileged):
        state.side_effect = [
            {"ready": False, "initialized": False, "status": ""},
            {"ready": False, "initialized": False, "status": ""},
            {"ready": True, "initialized": True, "status": "Session: RUNNING\nContainer: RUNNING"}
        ]
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(android.enable(), 0)
        self.assertTrue(settings.load()["android_enabled"])
        privileged.assert_called_once()
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(events[0]["phase"], "preparing")
        self.assertEqual(events[-1]["phase"], "ready")
        self.assertTrue(events[-1]["ready"])

    @patch("prismos.android.privileged_setup")
    @patch("prismos.android.subprocess.Popen")
    @patch("prismos.android.run", return_value="")
    @patch("prismos.android.status")
    @patch("prismos.android.shutil.which", return_value="/usr/bin/waydroid")
    def test_existing_container_skips_admin_prompt(self, which, state, run, popen, privileged):
        state.side_effect = [
            {"ready": False, "initialized": True, "status": "Container: RUNNING"},
            {"ready": False, "initialized": True, "status": "Container: RUNNING"},
            {"ready": True, "initialized": True, "status": "Session: RUNNING\nContainer: RUNNING"}
        ]
        with contextlib.redirect_stdout(io.StringIO()):
            android.enable()
        privileged.assert_not_called()

    @patch("prismos.android.run", return_value="")
    @patch("prismos.android.shutil.which", return_value="/usr/bin/waydroid")
    def test_disable_preserves_onboarding_and_data(self, which, run):
        settings.update(android_enabled=True, onboarding_complete=True)
        with patch("prismos.android.status", return_value={"ok": True, "enabled": False}):
            android.disable()
        self.assertFalse(settings.load()["android_enabled"])
        self.assertTrue(settings.load()["onboarding_complete"])
        run.assert_called_once_with(["waydroid", "session", "stop"], timeout=20)

    @patch("prismos.android.subprocess.Popen")
    @patch("prismos.android.settings.load", return_value={ "android_enabled": False })
    def test_resume_never_downloads_if_not_opted_in(self, load, popen):
        self.assertTrue(android.resume()["skipped"])
        popen.assert_not_called()

    def test_fdroid_rejects_redirect_to_untrusted_host(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = "https://example.net/malware.apk"
        with patch("prismos.android.urlopen", return_value=response):
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(CommandError):
                    android.download_fdroid(Path(tmp) / "f.apk")


if __name__ == "__main__":
    unittest.main()
