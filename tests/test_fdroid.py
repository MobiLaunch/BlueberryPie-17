import contextlib
import io
import json
import unittest
from unittest.mock import patch, MagicMock
from prismos import cli, fdroid
from prismos.system import CommandError


class FdroidCatalogTests(unittest.TestCase):
    def test_package_id_rejects_untrusted_uris_and_flags(self):
        for name in ("../../tmp", "--url", "evil;reboot", "com.foo/../bar", "",
                     "https://example.org/"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                fdroid.package_id(name)

    def test_normalizes_search_response_and_deduplicates(self):
        payload = {"apps": [{"packageName": "org.example.Game", "name": "Fun",
                             "summary": "Play", "categories": ["Games"]},
                            {"packageName": "org.example.Game", "name": "Duplicate"},
                            {"packageName": "../../tmp", "name": "Bad"}]}
        self.assertEqual(fdroid.normalized_results(payload), [{
            "id": "org.example.Game", "name": "Fun", "description": "Play",
            "categories": ["Games"], "source": "F-Droid", "kind": "android",
            "installed": False}])

    @patch("prismos.fdroid.android.status", return_value={"enabled": False})
    @patch("prismos.fdroid.urlopen")
    def test_off_does_not_send_network_requests(self, request, state):
        self.assertEqual(fdroid.search("game")["items"], [])
        request.assert_not_called()

    @patch("prismos.fdroid.android.status", return_value={"enabled": True})
    @patch("prismos.fdroid.urlopen")
    def test_search_uses_official_endpoint_and_bounded_json(self, opener, state):
        response = MagicMock()
        response.__enter__.return_value = response
        response.geturl.return_value = fdroid.SEARCH_URL + "?q=game"
        response.read.return_value = b'[{"packageName":"org.example.Game","name":"Game"}]'
        opener.return_value = response
        result = fdroid.search("game")
        self.assertEqual(result["items"][0]["id"], "org.example.Game")
        self.assertEqual(opener.call_args.args[0].full_url,
                         fdroid.SEARCH_URL + "?q=game")
        response.read.assert_called_once_with(fdroid.MAX_RESPONSE + 1)

    @patch("prismos.fdroid.android.status", return_value={
        "enabled": True, "ready": True, "fdroid_installed": True})
    @patch("prismos.fdroid.run")
    def test_details_handoff_is_fixed_verified_package_url(self, run, state):
        fdroid.details("org.example.Game")
        run.assert_called_once_with(
            ["waydroid", "app", "intent", "android.intent.action.VIEW",
             "https://f-droid.org/packages/org.example.Game/"], timeout=18)

    @patch("prismos.fdroid.android.status", return_value={
        "enabled": True, "ready": False, "fdroid_installed": False})
    @patch("prismos.fdroid.run")
    def test_details_refuses_uninitialized_android(self, run, state):
        with self.assertRaises(ValueError):
            fdroid.details("org.example.Game")
        run.assert_not_called()

    @patch("prismos.fdroid.android.status", return_value={"enabled": False})
    def test_cli_search_returns_json(self, state):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = cli.main(["fdroid", "search", "game"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["items"], [])


if __name__ == "__main__":
    unittest.main()
