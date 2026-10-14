import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from prismos import apps, cli, settings, system, theme


class IsolatedConfig(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.env = patch.dict(os.environ, {"XDG_CONFIG_HOME":self.temp.name})
        self.env.start()
        self.addCleanup(self.env.stop)


class SettingsTests(IsolatedConfig):
    def test_bad_json_falls_back(self):
        settings.directory().mkdir()
        (settings.directory()/"settings.json").write_text("{broken")
        self.assertEqual(settings.load(), settings.DEFAULTS)

    def test_invalid_types_do_not_break_theme(self):
        settings.directory().mkdir()
        (settings.directory()/"settings.json").write_text(json.dumps({"dark":"yes", "seed":3, "dnd":[], "unknown":True}))
        self.assertEqual(settings.load(), settings.DEFAULTS)

    def test_settings_are_persistent_and_private(self):
        settings.toggle("dark")
        self.assertTrue(settings.load()["dark"])
        self.assertEqual((settings.directory()/"settings.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(settings.directory().stat().st_mode & 0o777, 0o700)

    def test_concurrent_toggles_do_not_lose_updates(self):
        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(lambda _: settings.toggle("dnd"),range(11)))
        self.assertTrue(settings.load()["dnd"])
        self.assertFalse(list(settings.directory().glob(".settings-*")))

    def test_unknown_preferences_rejected(self):
        with self.assertRaises(ValueError): settings.toggle("anything")


class ColorTests(unittest.TestCase):
    def test_semantic_text_pairs_pass_contrast(self):
        seeds = list(theme.PALETTES.values()) + ["#ff0000","#00ff00","#0000ff","#000000","#ffffff","#888888"]
        pairs = [(name,"on"+name[0].upper()+name[1:]) for name in ("primary","primaryStrong","secondary","tertiary","surface","surfaceContainer","surfaceHigh","error")]
        for seed in seeds:
            for dark in (False,True):
                colors = theme.palette(seed,dark)
                for background, foreground in pairs:
                    with self.subTest(seed=seed,dark=dark,role=background):
                        self.assertGreaterEqual(theme.contrast(colors[background],colors[foreground]),4.5)

    def test_invalid_seeds_rejected(self):
        for value in ("red","#abc","$(echo bad)","#aaaaaa;touch /tmp/oops",None):
            with self.subTest(value=value), self.assertRaises(ValueError): theme.palette(value)

    def test_generated_tokens_match_native_generator(self):
        tokens = json.loads((Path(__file__).resolve().parent.parent/"design/tokens.json").read_text())
        for name, seed in theme.PALETTES.items():
            self.assertEqual(tokens["palettes"][name]["light"],theme.palette(seed))
            self.assertEqual(tokens["palettes"][name]["dark"],theme.palette(seed,True))

    def test_wallpaper_extracts_color(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            image=Path(directory)/"mint.png"
            Image.new("RGB",(20,20),(71,132,106)).save(image)
            self.assertEqual(theme.wallpaper_seed(image),"#47846a")


class AdapterTests(unittest.TestCase):
    @patch("prismos.system.run", side_effect=system.CommandError("Not installed"))
    def test_missing_controls_report_unavailable(self, run):
        for reader in (system.wifi,system.bluetooth,system.volume,system.brightness):
            self.assertFalse(reader()["available"])

    @patch("prismos.system.run", side_effect=["enabled","My:WiFi:802-11-wireless\nWired:802-3-ethernet"])
    def test_network_name_containing_colon(self, run):
        self.assertEqual(system.wifi()["label"],"My:WiFi")

    @patch("prismos.system.run", return_value="Volume: 0.64 [MUTED]")
    def test_audio_parses_volume_and_mute(self, run):
        self.assertEqual(system.volume(),{"available":True,"value":64,"muted":True})

    @patch("prismos.system.run", return_value="Volume: 1.50")
    def test_overamplification_clamped_for_ui(self, run):
        self.assertEqual(system.volume()["value"],100)

    @patch("prismos.system.run", return_value="No default controller available")
    def test_missing_bluetooth_controller(self, run):
        self.assertFalse(system.bluetooth()["available"])

    @patch("prismos.system.run", side_effect=["250","500"])
    def test_backlight_reader_avoids_keyboard_leds(self, run):
        self.assertEqual(system.brightness(),{"available":True,"value":50})
        self.assertEqual(run.call_args_list[0].args[0],["brightnessctl","-c","backlight","get"])

    @patch("prismos.system.run", return_value="")
    def test_volume_uses_argument_array(self, run):
        system.action("volume","35")
        run.assert_called_once_with(["wpctl","set-volume","@DEFAULT_AUDIO_SINK@","35%"])

    @patch("prismos.system.run")
    def test_invalid_values_cannot_execute(self, run):
        for value in ("-1","101","nan","inf","1; reboot",None):
            with self.subTest(value=value),self.assertRaises((ValueError,TypeError)):
                system.action("volume",value)
        run.assert_not_called()

    @patch("prismos.system.run")
    def test_backlight_cannot_be_set_to_zero(self, run):
        with self.assertRaises(ValueError):system.action("brightness","0")
        run.assert_not_called()

    @patch("prismos.system.run")
    def test_unknown_actions_rejected(self, run):
        with self.assertRaises(ValueError):system.action("reboot; anything")
        run.assert_not_called()

    @patch("prismos.system.shutil.which",return_value="/usr/bin/test")
    @patch("prismos.system.subprocess.run",side_effect=subprocess.TimeoutExpired("test",4))
    def test_timeout_becomes_action_error(self, run, which):
        with self.assertRaises(system.CommandError): system.run(["test"])


class DesktopEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.user=Path(self.temp.name)/"user";self.system=Path(self.temp.name)/"system"
        for root in (self.user,self.system):(root/"applications").mkdir(parents=True)
        self.env=patch.dict(os.environ,{"XDG_DATA_HOME":str(self.user),"XDG_DATA_DIRS":str(self.system),"XDG_CURRENT_DESKTOP":"Hyprland:PrismOS"})
        self.env.start();self.addCleanup(self.env.stop)

    def desktop(self,name,content,user=False):
        root=self.user if user else self.system
        path=root/"applications"/name;path.parent.mkdir(exist_ok=True,parents=True)
        path.write_text("[Desktop Entry]\nType=Application\nName=Test App\nExec=app %U\n"+content)
        return path

    def test_hidden_override_hides_system_entry(self):
        self.desktop("test.desktop","");self.desktop("test.desktop","Hidden=true\n",user=True)
        self.assertEqual(apps.entries(),[])

    def test_no_display_and_desktop_filter(self):
        self.desktop("hidden.desktop","NoDisplay=true\n")
        self.desktop("gnome.desktop","OnlyShowIn=GNOME;\n")
        self.desktop("prism.desktop","OnlyShowIn=PrismOS;\n")
        self.assertEqual([app["id"] for app in apps.entries()],["prism.desktop"])

    def test_exec_percent_codes_are_not_config_interpolation(self):
        self.desktop("nested/browser.desktop","Comment=Open %U safely\n")
        self.assertEqual(apps.entries()[0]["id"],"nested-browser.desktop")

    @patch("prismos.apps.run",return_value="")
    def test_launch_resolves_known_entry_through_gio(self, run):
        path=self.desktop("test.desktop","Exec=app; echo ignored\n")
        self.assertTrue(apps.launch("test.desktop")["ok"])
        run.assert_called_once_with(["gio","launch",str(path.resolve())],timeout=8)

    @patch("prismos.apps.run")
    def test_unknown_id_cannot_launch_path(self, run):
        with self.assertRaises(ValueError):apps.launch("../../untrusted.desktop")
        run.assert_not_called()


class CliTests(IsolatedConfig):
    def test_cli_errors_are_json(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output): code=cli.main(["action","unknown"])
        self.assertEqual(code,1);self.assertFalse(json.loads(output.getvalue())["ok"])

    def test_custom_seed_is_persistent(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):code=cli.main(["theme","--seed","#47846a"])
        self.assertEqual(code,0);self.assertEqual(settings.load()["seed"],"#47846a")


if __name__ == "__main__":unittest.main()
