import contextlib
import io
import json
import unittest
from unittest.mock import patch, call
from prismos import android, cli, store


class StoreTests(unittest.TestCase):
    @patch("prismos.store.shutil.which", return_value=None)
    def test_flatpak_missing(self, which):
        self.assertFalse(store.status()["available"])

    @patch("prismos.store.shutil.which", return_value="/usr/bin/flatpak")
    @patch("prismos.store.run", return_value="flathub\n")
    def test_exact_remote(self, run, which):
        self.assertTrue(store.status()["configured"])

    @patch("prismos.store.shutil.which", return_value="/usr/bin/flatpak")
    @patch("prismos.store.run", side_effect=["flathub\n", "org.example.Game\tExample\tPlay\tflathub\norg.example.Other\tOther\tNo\tother\n", "org.example.Game\n"])
    def test_search(self, run, which):
        self.assertEqual(store.search("game")["items"],
                         [{"id":"org.example.Game","name":"Example","description":"Play","installed":True}])

    @patch("prismos.store.run")
    def test_unsafe_id_rejected(self, run):
        for identifier in ("a", "--filesystem=host", "bad;echo x", "../../etc/passwd"):
            with self.assertRaises(ValueError):
                store.change("install", identifier)
        run.assert_not_called()

    @patch("prismos.store.status", return_value={"available":True,"configured":True})
    @patch("prismos.store.installed_ids", return_value=set())
    @patch("prismos.store.run", return_value="")
    def test_install_is_user_only(self, run, ids, status):
        store.change("install", "org.example.Game")
        run.assert_called_once_with(["flatpak","install","--user","--noninteractive",
                                     "--assumeyes","flathub","org.example.Game"],timeout=900)

    @patch("prismos.store.shutil.which", return_value="/usr/bin/flatpak")
    @patch("prismos.store.run", side_effect=["", "flathub\n"])
    def test_setup_is_explicit(self, run, which):
        store.enable()
        self.assertEqual(run.call_args_list[0],
                         call(["flatpak","remote-add","--user","--if-not-exists","flathub",store.REMOTE_URL],timeout=90))

    @patch("prismos.android.shutil.which", return_value=None)
    def test_android_missing(self, which):
        self.assertFalse(android.status()["available"])

    def test_invalid_store_cli_returns_json(self):
        data = io.StringIO()
        with contextlib.redirect_stdout(data):
            code = cli.main(["store", "install", "bad id!"])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(data.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
