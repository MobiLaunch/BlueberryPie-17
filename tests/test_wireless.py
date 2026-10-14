import contextlib
import io
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from prismos import cli, wireless
from prismos.system import CommandError

ADDRESS = "AA:BB:CC:DD:EE:FF"
IDENTIFIER = "12345678-1234-1234-1234-123456789abc"
NETWORK = {"bssid": ADDRESS, "ssid": "Cafe:$(no shell)", "interface": "wlan0", "key": "wpa-psk",
           "supported": True, "secured": True, "connected": False, "profile": None}


class DiscoveryTests(unittest.TestCase):
    def test_escaped_fields_and_backslashes_round_trip(self):
        self.assertEqual(wireless.fields(r"AA\:BB:My\:Cafe\\WiFi:78:WPA2:*:wlan0"),
                         ["AA:BB", "My:Cafe\\WiFi", "78", "WPA2", "*", "wlan0"])

    @patch("prismos.wireless.profiles", return_value=[])
    @patch("prismos.wireless.system.wifi", return_value={"available": True, "enabled": True})
    @patch("prismos.wireless.run")
    def test_scan_prefers_connected_ap_and_decodes_names(self, run, state, profiles):
        run.return_value = (r"AA\:BB\:CC\:DD\:EE\:FF:Cafe\:Blue:20:WPA2:*:wlan0" + "\n" +
                            r"11\:22\:33\:44\:55\:66:Cafe\:Blue:99:WPA2::wlan0" + "\n" +
                            r"11\:22\:33\:44\:55\:77:Open:200:--::wlan0" + "\ninvalid:row")
        result = wireless.wifi_list(True)["networks"]
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["ssid"], "Cafe:Blue")
        self.assertEqual(result[0]["bssid"], ADDRESS)
        self.assertTrue(result[0]["connected"])
        self.assertFalse(result[1]["secured"])
        self.assertEqual(result[1]["signal"], 100)
        self.assertEqual(run.call_args.args[0][-1], "yes")

    def test_security_types_require_correct_configuration(self):
        expected = {"--": "", "WPA2": "wpa-psk", "WPA2 WPA3": "wpa-psk", "WPA3": "sae",
                    "WPA2 802.1X": None, "WEP": None, "OWE": None, "unknown": None}
        for security, key in expected.items():
            self.assertEqual(wireless.security_key(security), key)

    @patch("prismos.wireless.run")
    @patch("prismos.wireless.system.wifi", return_value={"available": False, "enabled": False})
    def test_no_adapter_does_not_scan(self, state, run):
        self.assertEqual(wireless.wifi_list()["networks"], [])
        run.assert_not_called()

    @patch("prismos.wireless.run")
    def test_profiles_read_only_public_properties(self, run):
        run.side_effect = [IDENTIFIER + ":802-11-wireless", "Cafe:Blue\nwpa-psk"]
        self.assertEqual(wireless.profiles(), [{"uuid": IDENTIFIER, "ssid": "Cafe:Blue", "key": "wpa-psk"}])
        self.assertNotIn("--show-secrets", str(run.call_args_list))


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.discovery = patch("prismos.wireless.wifi_list", return_value={"networks": [dict(NETWORK)]})
        self.discovery.start(); self.addCleanup(self.discovery.stop)

    @patch("prismos.wireless.run")
    def test_secret_uses_private_file_then_is_removed(self, run):
        secret_paths = []
        def command(args, **kwargs):
            self.assertNotIn("my:secret password", args)
            if "passwd-file" in args:
                path = Path(args[-1]); secret_paths.append(path)
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertEqual(path.parent.stat().st_mode & 0o777, 0o700)
                self.assertEqual(path.read_text(), "802-11-wireless-security.psk:my:secret password\n")
            return ""
        run.side_effect = command
        self.assertTrue(wireless.wifi_connect(ADDRESS, "wlan0", "my:secret password")["ok"])
        self.assertTrue(secret_paths)
        self.assertFalse(any(path.exists() for path in secret_paths))
        self.assertIn(NETWORK["ssid"], run.call_args_list[0].args[0])

    @patch("prismos.wireless.run")
    def test_failed_activation_cleans_secret_and_only_new_profile(self, run):
        paths = []
        def command(args, **kwargs):
            if "passwd-file" in args:
                paths.append(Path(args[-1]))
                raise CommandError("secret password echoed by tool")
            return ""
        run.side_effect = command
        with self.assertRaises(CommandError) as error:
            wireless.wifi_connect(ADDRESS, "wlan0", "secret password")
        self.assertNotIn("secret password", str(error.exception))
        self.assertFalse(paths[0].exists())
        self.assertIn("delete", run.call_args.args[0])

    @patch("prismos.wireless.run", side_effect=CommandError("No secrets"))
    def test_existing_profile_is_never_deleted_on_failure(self, run):
        with patch("prismos.wireless.wifi_list", return_value={"networks": [{**NETWORK, "profile": IDENTIFIER}]}):
            with self.assertRaises(CommandError): wireless.wifi_connect(ADDRESS, "wlan0")
        self.assertEqual(run.call_count, 1)
        self.assertNotIn("delete", run.call_args.args[0])

    @patch("prismos.wireless.run")
    def test_saved_profile_activates_without_password_or_new_profile(self, run):
        with patch("prismos.wireless.wifi_list", return_value={"networks": [{**NETWORK, "profile": IDENTIFIER}]}):
            wireless.wifi_connect(ADDRESS, "wlan0")
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0][5:7], ["uuid", IDENTIFIER])

    @patch("prismos.wireless.run", side_effect=["", "", CommandError("Denied")])
    def test_autoconnect_preference_failure_keeps_successful_connection(self, run):
        result = wireless.wifi_connect(ADDRESS, "wlan0", "password123")
        self.assertTrue(result["ok"])
        self.assertIn("warning", result)
        self.assertFalse(any("delete" in c.args[0] for c in run.call_args_list))

    @patch("prismos.wireless.run")
    def test_invalid_selections_and_secret_formats_do_not_execute(self, run):
        for bssid, interface, password in (("--help", "wlan0", "12345678"), (ADDRESS, ";reboot", "12345678"),
                (ADDRESS, "wlan0", "line1\nline2"), (ADDRESS, "wlan0", "short"),
                (ADDRESS, "wlan0", "z"*64), (ADDRESS, "wlan0", None), (ADDRESS, "wlan0", "")):
            with self.subTest(password=bool(password)), self.assertRaises(ValueError):
                wireless.wifi_connect(bssid, interface, password)
        run.assert_not_called()

    @patch("prismos.wireless.run")
    def test_disappeared_network_cannot_connect(self, run):
        with patch("prismos.wireless.wifi_list", return_value={"networks": []}):
            with self.assertRaises(CommandError): wireless.wifi_connect(ADDRESS, "wlan0", "12345678")
        run.assert_not_called()

    @patch("prismos.wireless.run")
    def test_new_enterprise_network_uses_advanced_setup(self, run):
        with patch("prismos.wireless.wifi_list", return_value={"networks": [{**NETWORK, "key": None, "supported": False}]}):
            with self.assertRaises(CommandError): wireless.wifi_connect(ADDRESS, "wlan0", "12345678")
        run.assert_not_called()

    @patch("prismos.wireless.run", return_value="")
    def test_disconnect_only_acts_on_a_connected_wifi_interface(self, run):
        with self.assertRaises(CommandError): wireless.wifi_disconnect("wlan0")
        run.assert_not_called()
        with patch("prismos.wireless.wifi_list", return_value={"networks": [{**NETWORK, "connected": True}]}):
            wireless.wifi_disconnect("wlan0")
        self.assertEqual(run.call_args.args[0], ["nmcli", "--wait", "10", "device", "disconnect", "wlan0"])


class BluetoothTests(unittest.TestCase):
    @patch("prismos.wireless.system.bluetooth", return_value={"available": True, "enabled": True})
    @patch("prismos.wireless.run")
    def test_device_status_is_parsed_and_scan_is_bounded(self, run, state):
        run.side_effect = ["", "Device " + ADDRESS + " Blue buds", "Paired: yes\nConnected: yes"]
        result = wireless.bluetooth_list(True)["devices"]
        self.assertEqual(result, [{"address": ADDRESS, "name": "Blue buds", "paired": True, "connected": True}])
        self.assertEqual(run.call_args_list[0].args[0], ["bluetoothctl", "--timeout", "6", "scan", "on"])

    @patch("prismos.wireless.run", return_value="Failed to connect: org.bluez.Error.Failed")
    def test_zero_exit_with_bluez_error_is_failure(self, run):
        with patch("prismos.wireless.bluetooth_list", return_value={"devices": [{"address": ADDRESS, "paired": True}]}):
            with self.assertRaises(CommandError): wireless.bluetooth_action("connect", ADDRESS)

    @patch("prismos.wireless.run")
    def test_unpaired_or_unknown_device_requires_pairing_agent(self, run):
        with patch("prismos.wireless.bluetooth_list", return_value={"devices": [{"address": ADDRESS, "paired": False}]}):
            with self.assertRaises(CommandError): wireless.bluetooth_action("connect", ADDRESS)
            with self.assertRaises(ValueError): wireless.bluetooth_action("trust", ADDRESS)
            with self.assertRaises(ValueError): wireless.bluetooth_action("connect", "--help")
        run.assert_not_called()

    @patch("prismos.wireless.run", return_value="Connection successful")
    def test_paired_action_uses_fixed_arguments(self, run):
        with patch("prismos.wireless.bluetooth_list", return_value={"devices": [{"address": ADDRESS, "paired": True}]}):
            wireless.bluetooth_action("connect", ADDRESS.lower())
        self.assertEqual(run.call_args.args[0], ["bluetoothctl", "--timeout", "15", "connect", ADDRESS])


class SecretCliTests(unittest.TestCase):
    @patch("prismos.wireless.wifi_connect", return_value={"ok": True})
    def test_cli_reads_json_password_only_from_stdin(self, connect):
        output = io.StringIO()
        with patch("sys.stdin", io.StringIO(json.dumps({"password": "secret:input"})+"\n")), contextlib.redirect_stdout(output):
            code = cli.main(["wifi", "connect", "--bssid", ADDRESS, "--interface", "wlan0", "--password-stdin"])
        self.assertEqual(code, 0)
        connect.assert_called_once_with(ADDRESS, "wlan0", "secret:input")
        self.assertNotIn("secret:input", output.getvalue())

    @patch("prismos.wireless.wifi_connect")
    def test_malformed_secret_input_returns_json_without_echo(self, connect):
        for value in ('not json', '[]', '{"password":"' + 'x'*2000):
            output = io.StringIO()
            with patch("sys.stdin", io.StringIO(value)), contextlib.redirect_stdout(output):
                code = cli.main(["wifi", "connect", "--password-stdin"])
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(output.getvalue())["error"], "Invalid password input")
        connect.assert_not_called()
