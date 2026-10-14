import contextlib
import io
import json
import unittest
from unittest.mock import patch

from prismos import audio, cli, system
from prismos.system import CommandError


def node(identifier, serial, kind="Audio/Sink", name="speakers", label="Built-in speakers"):
    return {"id": identifier, "type": "PipeWire:Interface:Node", "info": {"props": {
        "object.serial": serial, "media.class": kind, "node.name": name, "node.description": label}}}


def metadata(sink="speakers", source="microphone"):
    return {"id": 1, "type": "PipeWire:Interface:Metadata", "props": {"metadata.name": "default"},
            "metadata": [{"subject": 0, "key": "default.audio.sink", "value": {"name": sink}},
                         {"subject": 0, "key": "default.audio.source", "value": json.dumps({"name": source})}]}


GRAPH = [node(42, 1042), node(43, "1043", name="headphones", label="Blue buds"),
         node(54, 1054, "Audio/Source", "microphone", "Internal microphone"), metadata()]


class DiscoveryTests(unittest.TestCase):
    @patch("prismos.audio.run", return_value=json.dumps(GRAPH))
    def test_json_nodes_have_stable_serials_and_default_metadata(self, run):
        result = audio.graph()
        self.assertEqual(len(result), 3)
        self.assertEqual(next(d for d in result if d["name"] == "speakers")["serial"], "1042")
        self.assertTrue(next(d for d in result if d["name"] == "microphone")["selected"])
        self.assertFalse(next(d for d in result if d["name"] == "headphones")["selected"])
        run.assert_called_once_with(["pw-dump", "--no-colors"], timeout=5)

    @patch("prismos.audio.run")
    def test_streams_monitors_invalid_ids_and_missing_properties_are_excluded(self, run):
        rows = [node(1, 1, "Stream/Output/Audio"), node(2, 2, "Audio/Source", "sink.monitor"),
                node(True, 3), node(4, True), node(-1, 5), None, {"info": None}, {"info": {"props": []}}]
        run.return_value = json.dumps(rows)
        self.assertEqual(audio.graph(), [])

    @patch("prismos.audio.run")
    def test_duplicate_serial_is_not_a_second_device(self, run):
        run.return_value = json.dumps([node(42, 1042), node(43, 1042)])
        self.assertEqual(len(audio.graph()), 1)

    @patch("prismos.audio.run")
    def test_absent_default_does_not_guess_the_first_device(self, run):
        run.return_value = json.dumps([node(42, 1042)])
        result = audio.snapshot()
        self.assertTrue(result["available"])
        self.assertIsNone(result["output"])
        self.assertIsNone(result["input"])
        self.assertEqual(len(result["outputs"]), 1)

    @patch("prismos.audio.run")
    def test_configured_and_non_global_metadata_do_not_override_actual_default(self, run):
        actual = metadata()
        actual["metadata"] += [{"subject": 9, "key": "default.audio.sink", "value": {"name": "headphones"}},
                               {"subject": 0, "key": "default.configured.audio.sink", "value": {"name": "headphones"}},
                               {"subject": 0, "key": [], "value": {}}, {"subject": 0, "key": "default.audio.source", "value": "invalid JSON"}]
        run.return_value = json.dumps(GRAPH[:-1] + [actual])
        self.assertTrue(next(d for d in audio.graph() if d["name"] == "speakers")["selected"])

    @patch("prismos.audio.run")
    def test_malformed_server_data_and_missing_service_return_unavailable(self, run):
        for data in ("not JSON", "{}", "null"):
            run.return_value = data
            self.assertFalse(audio.snapshot()["available"])
        run.side_effect = CommandError("No PipeWire server")
        self.assertEqual(audio.snapshot()["outputs"], [])

    @patch("prismos.audio.run", return_value=json.dumps(GRAPH))
    @patch("prismos.audio.level", return_value={"available": True, "value": 55, "muted": True})
    def test_selected_devices_receive_volume_and_mute_state(self, level, run):
        result = audio.snapshot()
        self.assertEqual(result["output"]["label"], "Built-in speakers")
        self.assertEqual(result["output"]["value"], 55)
        self.assertTrue(result["input"]["muted"])
        self.assertEqual({c.args[0] for c in level.call_args_list}, {42, 54})


class VolumeTests(unittest.TestCase):
    @patch("prismos.audio.run", return_value="Volume: 0.48 [MUTED]")
    def test_microphone_default_uses_source_alias(self, run):
        self.assertEqual(audio.default_level("input"), {"available": True, "value": 48, "muted": True})
        run.assert_called_once_with(["wpctl", "get-volume", "@DEFAULT_AUDIO_SOURCE@"])

    @patch("prismos.audio.run", return_value="Volume: 1.50")
    def test_overamplified_read_is_clamped_for_ui(self, run):
        self.assertEqual(audio.level(42)["value"], 100)

    @patch("prismos.audio.run")
    def test_invalid_volume_output_does_not_crash(self, run):
        for data in ("Volume: 0..5", "Volume: NaN", "Volume: -1", "unknown", "Volume: " + "9"*400):
            run.return_value = data
            self.assertFalse(audio.level(42)["available"])


class ActionTests(unittest.TestCase):
    def setUp(self):
        self.device = {"id": 42, "serial": "1042", "name": "speakers", "kind": "output"}
        context = patch("prismos.audio.graph", return_value=[self.device])
        context.start(); self.addCleanup(context.stop)

    @patch("prismos.audio.run", return_value="")
    def test_select_resolves_serial_to_current_node(self, run):
        audio.action("select", "output", "1042", "speakers")
        run.assert_called_once_with(["wpctl", "set-default", "42"])

    @patch("prismos.audio.run", return_value="")
    def test_node_id_can_change_without_reusing_cached_id(self, run):
        self.device["id"] = 99
        audio.action("select", "output", "1042", "speakers")
        self.assertEqual(run.call_args.args[0][-1], "99")

    @patch("prismos.audio.run")
    def test_disappeared_serial_wrong_kind_or_changed_name_cannot_write(self, run):
        for kind, serial, name in (("output", "9999", "speakers"), ("input", "1042", "speakers"), ("output", "1042", "different-device")):
            with self.assertRaises(CommandError): audio.action("select", kind, serial, name)
        run.assert_not_called()

    @patch("prismos.audio.run", return_value="")
    def test_volume_zero_is_allowed_and_amplification_is_limited(self, run):
        audio.action("volume", "output", "1042", "speakers", "0")
        run.assert_called_once_with(["wpctl", "set-volume", "42", "0%", "--limit", "1.0"])

    @patch("prismos.audio.run", return_value="")
    def test_microphone_mute_is_explicit_and_does_not_touch_output(self, run):
        self.device["kind"] = "input"
        audio.action("mute", "input", "1042", "speakers", "1")
        run.assert_called_once_with(["wpctl", "set-mute", "42", "1"])

    @patch("prismos.audio.run")
    def test_invalid_percentages_and_actions_do_not_write(self, run):
        for value in ("-1", "101", "NaN", "inf", None, "50; reboot"):
            with self.assertRaises(ValueError): audio.action("volume", "output", "1042", "speakers", value)
        for value in (None, "toggle", "2", "1; reboot"):
            with self.assertRaises(ValueError): audio.action("mute", "output", "1042", "speakers", value)
        for serial in (None, True, "-1", "--help", "1; reboot", "18446744073709551616"):
            with self.assertRaises(ValueError): audio.action("select", "output", serial, "speakers")
        with self.assertRaises(ValueError): audio.action("remove", "output", "1042", "speakers")
        run.assert_not_called()

    @patch("prismos.audio.run", side_effect=CommandError("Device vanished"))
    def test_command_failure_is_reported_without_false_success(self, run):
        with self.assertRaises(CommandError): audio.action("select", "output", "1042", "speakers")

    @patch("prismos.system.run", return_value="")
    def test_quick_mic_action_uses_only_default_source(self, run):
        system.action("microphone-mute")
        run.assert_called_once_with(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])


class CliTests(unittest.TestCase):
    @patch("prismos.audio.action", return_value={"ok": True})
    def test_device_identity_is_passed_as_separate_arguments(self, action):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = cli.main(["audio", "select", "--kind", "output", "--serial", "1042", "--node-name=odd;$(literal)"])
        self.assertEqual(result, 0)
        action.assert_called_once_with("select", "output", "1042", "odd;$(literal)", None)

    def test_missing_device_returns_json_error(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output): result = cli.main(["audio", "select"])
        self.assertEqual(result, 1)
        self.assertFalse(json.loads(output.getvalue())["ok"])
