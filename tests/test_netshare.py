import contextlib
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prismos import cli, hotspot, settings, system, vpn
from prismos.system import CommandError

UUID_A = "11111111-2222-3333-4444-555555555555"
UUID_B = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


class Isolated(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name + "/config", "XDG_DATA_HOME": self.temp.name + "/data"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def call(self, argv, stdin=""):
        with patch("sys.stdin", io.StringIO(stdin)), contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(argv)
        return code, json.loads(out.getvalue())


class FakeNmcli:
    """Answers the nmcli calls the hotspot makes and records every command."""

    def __init__(self, profile=None, active=False, ap="yes", wifi=True):
        self.calls = []
        self.profile, self.active, self.ap, self.wifi = profile, active, ap, wifi
        self.secret_seen = None

    def __call__(self, args, timeout=4):
        self.calls.append(list(args))
        if args[:2] == ["nmcli", "-t"] and "DEVICE,TYPE" in args:
            return "wlan0:wifi\nlo:loopback" if self.wifi else "lo:loopback"
        if "WIFI-PROPERTIES.AP" in args:
            return self.ap
        if "NAME,TYPE,ACTIVE" in args:
            return f"{hotspot.NAME}:802-11-wireless:{'yes' if self.active else 'no'}\nHome:802-11-wireless:no" if self.profile else "Home:802-11-wireless:no"
        if "passwd-file" in args:
            path = Path(args[args.index("passwd-file") + 1])
            self.secret_seen = (path.read_text(), stat.S_IMODE(path.stat().st_mode))
        return ""


class HotspotTests(Isolated):
    def test_names_and_passwords_are_validated(self):
        self.assertEqual(hotspot.clean_ssid("  My phone  "), "My phone")
        for bad in ("", "   ", "x" * 33, "tab\there", "é" * 17, None, 5):
            with self.subTest(ssid=bad), self.assertRaises(ValueError):
                hotspot.clean_ssid(bad)
        self.assertEqual(hotspot.clean_password("abcdefgh"), "abcdefgh")
        for bad in ("short", "x" * 64, "pässwörd1", "line\nbreak1", None):
            with self.subTest(password=bad), self.assertRaises(ValueError):
                hotspot.clean_password(bad)

    def test_a_default_is_generated_valid_and_random(self):
        config = hotspot.load()
        self.assertTrue(config["ssid"].startswith("PrismOS-"))
        self.assertEqual(len(config["password"]), hotspot.PASSWORD_LENGTH)
        self.assertTrue(set(config["password"]) <= set(hotspot.ALPHABET))
        self.assertEqual(hotspot.clean_ssid(config["ssid"]), config["ssid"])
        self.assertNotEqual(hotspot.make_password(), hotspot.make_password())

    def test_the_first_password_is_saved_so_every_later_read_agrees(self):
        first = hotspot.load()
        self.assertTrue(hotspot.config_path().exists())
        self.assertEqual(hotspot.load(), first)
        with patch("prismos.hotspot.run", FakeNmcli()):
            self.assertEqual(hotspot.info()["password"], first["password"])

    def test_the_saved_file_is_private_and_a_damaged_one_is_replaced(self):
        hotspot.save({"ssid": "Mine", "password": "correct-horse"})
        path = hotspot.config_path()
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
        self.assertEqual(hotspot.load(), {"ssid": "Mine", "password": "correct-horse"})
        path.write_text('{"ssid": "ok", "password": "x"}')
        self.assertTrue(hotspot.load()["ssid"].startswith("PrismOS-"), "a too-short password is not trusted")
        path.write_text("not json")
        self.assertEqual(len(hotspot.load()["password"]), hotspot.PASSWORD_LENGTH)

    @patch("prismos.hotspot.shutil.which", return_value="/usr/bin/dnsmasq")
    def test_turning_it_on_never_puts_the_password_in_a_command_line(self, which):
        fake = FakeNmcli()
        with patch("prismos.hotspot.run", fake):
            self.assertEqual(hotspot.enable(), {"ok": True, "enabled": True})
        password = hotspot.load()["password"]
        for call in fake.calls:
            self.assertNotIn(password, " ".join(call), call)
        add = next(call for call in fake.calls if call[:3] == ["nmcli", "connection", "add"])
        self.assertIn("802-11-wireless-security.psk-flags", add)
        self.assertEqual(add[add.index("802-11-wireless-security.psk-flags") + 1], "2", "NetworkManager keeps no copy")
        self.assertIn("shared", add)
        self.assertEqual(fake.secret_seen, (f"802-11-wireless-security.psk:{password}\n", 0o600))
        self.assertTrue(hotspot.config_path().exists())
        # The temporary password file is gone afterwards.
        up = next(call for call in fake.calls if "passwd-file" in call)
        self.assertFalse(Path(up[up.index("passwd-file") + 1]).exists())

    @patch("prismos.hotspot.shutil.which", return_value="/usr/bin/dnsmasq")
    def test_an_existing_profile_is_updated_and_an_active_hotspot_is_left_alone(self, which):
        fake = FakeNmcli(profile=True)
        with patch("prismos.hotspot.run", fake):
            hotspot.enable()
        self.assertTrue(any(call[:3] == ["nmcli", "connection", "modify"] for call in fake.calls))
        self.assertFalse(any(call[:3] == ["nmcli", "connection", "add"] for call in fake.calls))
        running = FakeNmcli(profile=True, active=True)
        with patch("prismos.hotspot.run", running):
            self.assertEqual(hotspot.enable(), {"ok": True, "enabled": True})
        self.assertFalse(any("up" in call for call in running.calls))

    @patch("prismos.hotspot.shutil.which", return_value="/usr/bin/dnsmasq")
    def test_failures_give_fixed_messages_that_never_echo_settings(self, which):
        for kwargs, message in (({"wifi": False}, "No Wi-Fi adapter"), ({"ap": "no"}, "cannot host a hotspot")):
            with self.subTest(message=message), patch("prismos.hotspot.run", FakeNmcli(**kwargs)):
                with self.assertRaisesRegex(CommandError, message):
                    hotspot.enable()
        failing = FakeNmcli()

        def run(args, timeout=4):
            if "passwd-file" in args:
                raise CommandError("Error: secret " + hotspot.load()["password"])
            return failing(args, timeout)
        with patch("prismos.hotspot.run", run):
            with self.assertRaises(CommandError) as raised:
                hotspot.enable()
        self.assertNotIn(hotspot.load()["password"], str(raised.exception))

    @patch("prismos.hotspot.shutil.which", return_value=None)
    def test_without_dnsmasq_it_says_so(self, which):
        with patch("prismos.hotspot.run", FakeNmcli()), self.assertRaisesRegex(CommandError, "dnsmasq"):
            hotspot.enable()

    def test_turning_it_off_only_acts_when_it_is_on(self):
        for active in (False, True):
            fake = FakeNmcli(profile=True, active=active)
            with patch("prismos.hotspot.run", fake):
                self.assertEqual(hotspot.disable(), {"ok": True, "enabled": False})
            self.assertEqual(any("down" in call for call in fake.calls), active)

    def test_status_reads_the_connection_list(self):
        rows = [["Home", "802-11-wireless", "yes"], [hotspot.NAME, "802-11-wireless", "yes"]]
        self.assertEqual(hotspot.status(rows)["enabled"], True)
        self.assertEqual(hotspot.status([["Home", "802-11-wireless", "yes"]])["enabled"], False)
        with patch("prismos.hotspot.run", side_effect=CommandError("nmcli is not installed")):
            self.assertEqual(hotspot.status()["available"], False)

    def test_changing_the_name_or_password_is_saved_and_applied_when_next_turned_on(self):
        fake = FakeNmcli(profile=True, active=False)
        with patch("prismos.hotspot.run", fake):
            result = hotspot.configure(ssid=" Cafe ", password="new-password-1")
        self.assertEqual((result["ssid"], result["password"], result["restart_needed"]), ("Cafe", "new-password-1", False))
        self.assertTrue(any("802-11-wireless.ssid" in call for call in fake.calls))
        again = FakeNmcli(profile=True, active=True)
        with patch("prismos.hotspot.run", again):
            changed = hotspot.configure(regenerate=True)
        self.assertTrue(changed["restart_needed"])
        self.assertNotEqual(changed["password"], "new-password-1")
        self.assertFalse(any("modify" in call for call in again.calls), "a running hotspot is not touched")
        for bad in ({"ssid": ""}, {"password": "short"}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                hotspot.configure(**bad)

    def test_the_password_is_copied_through_a_pipe(self):
        with patch("prismos.hotspot.shutil.which", return_value="/usr/bin/wl-copy"), \
                patch("prismos.hotspot.subprocess.run") as run:
            hotspot.copy_password()
        self.assertEqual(run.call_args.args[0], ["wl-copy"])
        self.assertEqual(run.call_args.kwargs["input"], hotspot.load()["password"])

    def test_the_cli_reads_settings_from_stdin_and_rejects_nonsense(self):
        with patch("prismos.hotspot.run", FakeNmcli(profile=True)):
            code, result = self.call(["hotspot", "set"], json.dumps({"ssid": "Desk", "password": "abcdefgh1"}))
        self.assertEqual((code, result["ssid"]), (0, "Desk"))
        self.assertEqual(self.call(["hotspot", "set"], "[1]")[0], 1)
        self.assertEqual(self.call(["hotspot", "set"], "nope")[0], 1)


class VpnTests(Isolated):
    RAW = (f"Home Wi-Fi:99999999-9999-9999-9999-999999999999:802-11-wireless:yes\n"
           f"Work: Paris:{UUID_A}:vpn:no\n"
           f"wg0:{UUID_B}:wireguard:yes\n"
           "Broken:not-a-uuid:vpn:no\n"
           f"Bridge:{UUID_A.replace('1', '2')}:bridge:no\n")

    def test_only_vpn_and_wireguard_profiles_with_real_uuids_are_listed(self):
        found = vpn.rows_from(self.RAW)
        self.assertEqual([(p["name"], p["active"]) for p in found], [("Work: Paris", False), ("wg0", True)])

    def test_status_names_the_connected_vpn_or_the_one_that_would_connect(self):
        found = vpn.rows_from(self.RAW)
        self.assertEqual(vpn.status(found), {"available": True, "enabled": True, "count": 2, "label": "wg0"})
        idle = [{**p, "active": False} for p in found]
        self.assertEqual(vpn.status(idle)["label"], "Work: Paris")
        self.assertEqual(vpn.status([])["available"], False)

    def run_with(self, raw, record):
        def run(args, timeout=4):
            record.append(list(args))
            return raw if "NAME,UUID,TYPE,ACTIVE" in args else ""
        return patch("prismos.vpn.run", run)

    def test_toggle_disconnects_an_active_vpn_or_connects_the_preferred_one(self):
        record = []
        with self.run_with(self.RAW, record):
            vpn.toggle()
        self.assertIn(["nmcli", "--wait", "10", "connection", "down", "uuid", UUID_B], record)
        idle = self.RAW.replace(":wireguard:yes", ":wireguard:no")
        record.clear()
        with self.run_with(idle, record):
            vpn.toggle()
        self.assertIn(["nmcli", "--wait", "30", "connection", "up", "uuid", UUID_A], record, "the first profile when none was chosen")
        self.assertEqual(settings.load()["vpn_profile"], UUID_A)

    def test_choosing_a_profile_makes_it_the_one_the_tile_uses(self):
        idle = self.RAW.replace(":wireguard:yes", ":wireguard:no")
        record = []
        with self.run_with(idle, record):
            self.assertEqual(vpn.choose(UUID_B.upper())["preferred"], UUID_B)
            vpn.toggle()
        self.assertIn(["nmcli", "--wait", "30", "connection", "up", "uuid", UUID_B], record)

    def test_unknown_or_malformed_choices_are_refused_and_nothing_runs(self):
        record = []
        with self.run_with(self.RAW, record):
            for bad in (None, "", "x", "11111111-2222-3333-4444-000000000000", "$(reboot)"):
                with self.subTest(uuid=bad), self.assertRaises(ValueError):
                    vpn.connect(bad)
        self.assertFalse(any("up" in call for call in record))

    def test_secret_prompts_become_a_helpful_message(self):
        idle = self.RAW.replace(":wireguard:yes", ":wireguard:no")

        def run(args, timeout=4):
            if "up" in args:
                raise CommandError("Error: Connection activation failed: Secrets were required, but not provided")
            return idle
        with patch("prismos.vpn.run", run), self.assertRaisesRegex(CommandError, "password or token"):
            vpn.toggle()

    def test_no_vpn_set_up_says_so(self):
        with patch("prismos.vpn.run", return_value="Home:99999999-9999-9999-9999-999999999999:802-11-wireless:yes"):
            with self.assertRaisesRegex(CommandError, "No VPN"):
                vpn.toggle()

    def test_a_corrupt_saved_profile_choice_is_ignored(self):
        settings.update(vpn_profile=UUID_B)
        path = settings.directory() / "settings.json"
        data = json.loads(path.read_text())
        data["vpn_profile"] = "'; rm -rf /"
        path.write_text(json.dumps(data))
        self.assertEqual(settings.load()["vpn_profile"], "")


class StatusAndTileTests(Isolated):
    def test_status_carries_hotspot_and_vpn_from_one_nmcli_call(self):
        calls = []

        def run(args, timeout=4):
            calls.append(list(args))
            return (f"{hotspot.NAME}:{UUID_A}:802-11-wireless:yes\nwg0:{UUID_B}:wireguard:no")
        with patch("prismos.system.run", run):
            result = system.connections()
        self.assertEqual(len(calls), 1)
        self.assertEqual(result["hotspot"]["enabled"], True)
        self.assertEqual((result["vpn"]["available"], result["vpn"]["enabled"], result["vpn"]["count"]), (True, False, 1))

    def test_a_missing_nmcli_marks_both_unavailable(self):
        with patch("prismos.system.run", side_effect=CommandError("nmcli is not installed")):
            result = system.connections()
        self.assertFalse(result["hotspot"]["available"])
        self.assertFalse(result["vpn"]["available"])

    def test_the_hotspot_dependency_is_packaged(self):
        root = Path(__file__).resolve().parent.parent
        self.assertIn("'dnsmasq'", (root / "packaging/arch/PKGBUILD").read_text())
        self.assertIn("dnsmasq", (root / "archiso/packages.x86_64").read_text().split())

    def test_the_tiles_exist_and_can_be_chosen(self):
        from prismos import tiles
        self.assertIn("hotspot", tiles.IDS)
        self.assertIn("vpn", tiles.IDS)
        self.assertEqual(tiles.change(["wifi", "hotspot", "vpn"])["enabled"], ["wifi", "hotspot", "vpn"])


if __name__ == "__main__":
    unittest.main()
