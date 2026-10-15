import contextlib
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from prismos import cli, notifyprefs, settings, system, tiles
from prismos.system import CommandError


class Isolated(unittest.TestCase):
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


class TileTests(Isolated):
    def test_defaults_are_the_original_eight_tiles(self):
        self.assertEqual(tiles.enabled(), ["wifi", "bluetooth", "sound", "microphone", "dnd", "dark",
                                           "reduced_motion", "audio_devices"])

    def test_order_and_selection_persist(self):
        code, result = self.call(["tiles", "set", "dark", "wifi", "airplane", "dark"])
        self.assertEqual((code, result["enabled"]), (0, ["dark", "wifi", "airplane"]))
        self.assertEqual(self.call(["tiles", "list"])[1]["enabled"], ["dark", "wifi", "airplane"])
        self.call(["tiles", "reset"])
        self.assertEqual(len(tiles.enabled()), 8)

    def test_unknown_or_empty_selections_are_refused(self):
        for ids in (["wifi", "../x"], [], ["rm -rf"]):
            code, result = self.call(["tiles", "set", *ids])
            self.assertEqual(code, 1, ids)
            self.assertFalse(result["ok"])
        self.assertIsNone(settings.load()["tiles"])

    def test_corrupt_saved_tiles_are_filtered(self):
        settings.directory().mkdir()
        (settings.directory() / "settings.json").write_text('{"tiles": ["dark", "evil", "dark", 3, "wifi"]}')
        self.assertEqual(tiles.enabled(), ["dark", "wifi"])

    def test_catalog_matches_the_settings_allowlist(self):
        self.assertEqual(tiles.IDS, settings.TILE_IDS)


class NotificationMuteTests(Isolated):
    def test_mute_and_unmute_are_idempotent_data_only(self):
        self.assertEqual(self.call(["notifications", "mute", "Chat"])[1]["muted"], ["Chat"])
        self.assertEqual(self.call(["notifications", "mute", "Chat"])[1]["muted"], ["Chat"])
        self.call(["notifications", "mute", "Mail; rm -rf /"])
        self.assertEqual(settings.load()["muted_apps"], ["Chat", "Mail; rm -rf /"])
        self.assertEqual(self.call(["notifications", "unmute", "Chat"])[1]["muted"], ["Mail; rm -rf /"])

    def test_bad_names_and_the_limit_are_refused(self):
        for name in ("", "x" * 65, "a\nb", "\x00"):
            self.assertEqual(self.call(["notifications", "mute", name])[0], 1, repr(name))
        for index in range(notifyprefs.LIMIT):
            notifyprefs.mute(f"app{index}")
        self.assertEqual(self.call(["notifications", "mute", "one-more"])[0], 1)

    def test_saved_list_is_sanitized_on_load(self):
        settings.directory().mkdir()
        (settings.directory() / "settings.json").write_text(json.dumps({"muted_apps": ["ok", "ok", "bad\nname", 5, "z" * 80]}))
        self.assertEqual(settings.load()["muted_apps"], ["ok"])


class NewTileActionTests(Isolated):
    def radios(self, wifi_on=True, bt_on=True, wifi=True, bt=True):
        return {"wifi": {"available": wifi, "enabled": wifi_on}, "bluetooth": {"available": bt, "enabled": bt_on}}

    def test_airplane_state_means_every_present_radio_is_off(self):
        self.assertTrue(system.airplane(self.radios(False, False))["enabled"])
        self.assertFalse(system.airplane(self.radios(True, False))["enabled"])
        self.assertTrue(system.airplane(self.radios(False, True, bt=False))["enabled"])
        self.assertTrue(system.airplane(self.radios(False, bt=False))["enabled"])
        self.assertFalse(system.airplane(self.radios(wifi=False, bt=False))["available"])

    @patch("prismos.system.bluetooth", return_value={"available": True, "enabled": True})
    @patch("prismos.system.wifi", return_value={"available": True, "enabled": True, "label": "x"})
    @patch("prismos.system.run")
    def test_airplane_turns_everything_off_then_back_on(self, run, wifi, bluetooth):
        system.action("airplane")
        self.assertEqual([call.args[0] for call in run.call_args_list],
                         [["nmcli", "radio", "wifi", "off"], ["bluetoothctl", "power", "off"]])
        run.reset_mock()
        wifi.return_value = {"available": True, "enabled": False, "label": "Off"}
        bluetooth.return_value = {"available": True, "enabled": False}
        system.action("airplane")
        self.assertEqual([call.args[0] for call in run.call_args_list],
                         [["nmcli", "radio", "wifi", "on"], ["bluetoothctl", "power", "on"]])

    @patch("prismos.system.bluetooth", return_value={"available": False, "enabled": False})
    @patch("prismos.system.wifi", return_value={"available": False, "enabled": False, "label": ""})
    def test_airplane_without_radios_is_an_error(self, wifi, bluetooth):
        with self.assertRaises(CommandError):
            system.action("airplane")

    @patch("prismos.system.run")
    @patch("prismos.system.power_profile")
    def test_battery_saver_toggles_between_two_fixed_profiles(self, profile, run):
        profile.return_value = {"available": True, "profile": "balanced", "saver": False}
        system.action("battery-saver")
        run.assert_called_with(["powerprofilesctl", "set", "power-saver"])
        profile.return_value = {"available": True, "profile": "power-saver", "saver": True}
        system.action("battery-saver")
        run.assert_called_with(["powerprofilesctl", "set", "balanced"])
        profile.return_value = {"available": False, "profile": "", "saver": False}
        with self.assertRaises(CommandError):
            system.action("battery-saver")

    @patch("prismos.system.shutil.which", return_value=None)
    def test_power_profile_missing_tool_is_unavailable(self, which):
        self.assertFalse(system.power_profile()["available"])

    @patch("prismos.system.run", return_value="power-saver")
    @patch("prismos.system.shutil.which", return_value="/usr/bin/powerprofilesctl")
    def test_power_profile_reads_known_values_only(self, which, run):
        self.assertTrue(system.power_profile()["saver"])
        run.return_value = "evil; profile"
        self.assertFalse(system.power_profile()["available"])

    @patch("prismos.system.run")
    @patch("prismos.system.shutil.which", return_value="/usr/bin/hyprsunset")
    def test_night_light_applies_before_saving(self, which, run):
        system.action("night-light")
        run.assert_called_with(["hyprctl", "hyprsunset", "temperature", "3800"], timeout=5)
        self.assertTrue(settings.load()["night_light"])
        system.action("night-light")
        run.assert_called_with(["hyprctl", "hyprsunset", "identity"], timeout=5)
        self.assertFalse(settings.load()["night_light"])

    @patch("prismos.system.run", side_effect=CommandError("no daemon"))
    @patch("prismos.system.shutil.which", return_value="/usr/bin/hyprsunset")
    def test_failed_night_light_change_is_not_saved(self, which, run):
        with self.assertRaises(CommandError):
            system.action("night-light")
        self.assertFalse(settings.load()["night_light"])

    @patch("prismos.system.run")
    @patch("prismos.system.shutil.which", return_value="/usr/bin/hyprsunset")
    def test_session_start_reapplies_the_saved_state(self, which, run):
        settings.update(night_light=True)
        system.action("night-light-apply")
        run.assert_called_with(["hyprctl", "hyprsunset", "temperature", "3800"], timeout=5)
        self.assertTrue(settings.load()["night_light"])

    @patch("prismos.system.shutil.which", return_value=None)
    def test_night_light_without_hyprsunset_explains_itself(self, which):
        with self.assertRaisesRegex(CommandError, "hyprsunset"):
            system.action("night-light")


if __name__ == "__main__":
    unittest.main()
