import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from prismos import cli, notifyprefs, settings


class NotificationHistorySettingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def call(self, argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(argv)
        return code, json.loads(out.getvalue())

    def test_history_is_off_by_default(self):
        self.assertIs(settings.load()["notification_history"], False)
        self.assertEqual(notifyprefs.history_status(), {"ok": True, "enabled": False})

    def test_turning_it_on_and_off_persists(self):
        self.assertEqual(self.call(["notifications", "history", "yes"]), (0, {"ok": True, "enabled": True}))
        self.assertIs(settings.load()["notification_history"], True)
        self.assertEqual(self.call(["notifications", "history", "no"])[1]["enabled"], False)
        self.assertIs(settings.load()["notification_history"], False)

    def test_only_yes_or_no_is_accepted(self):
        for value in (None, "", "true", "1", "YES"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                notifyprefs.set_history(value)
        self.assertIs(settings.load()["notification_history"], False)

    def test_a_non_boolean_in_the_file_falls_back_to_off(self):
        settings.update(notification_history=True)
        path = settings.directory() / "settings.json"
        data = json.loads(path.read_text())
        data["notification_history"] = "yes"
        path.write_text(json.dumps(data))
        self.assertIs(settings.load()["notification_history"], False)


if __name__ == "__main__":
    unittest.main()
