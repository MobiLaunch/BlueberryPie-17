import contextlib
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from prismos import cli, recorder, settings
from prismos.system import CommandError

FAKE = (Path(__file__).parent / "fakes" / "wf-recorder").read_text()


class Isolated(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        runtime = Path(self.temp.name) / "run"
        runtime.mkdir(mode=0o700)
        self.fake = Path(self.temp.name) / "bin"
        self.fake.mkdir()
        (self.fake / "wf-recorder").write_text(FAKE)
        (self.fake / "wf-recorder").chmod(0o755)
        patcher = patch.dict(os.environ, {"HOME": self.temp.name, "XDG_CONFIG_HOME": self.temp.name + "/config",
                                          "XDG_RUNTIME_DIR": str(runtime),
                                          "PATH": f"{self.fake}:{os.environ['PATH']}"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.kill_leftovers)

    def kill_leftovers(self):
        state = recorder.read_state()
        if state:
            try:
                os.kill(state["pid"], 9)
            except OSError:
                pass

    def call(self, argv):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = cli.main(argv)
        return code, json.loads(out.getvalue())


class RealProcessTests(Isolated):
    def test_a_recording_can_be_started_watched_and_stopped(self):
        with patch("prismos.recorder.focused_output", return_value=None):
            started = recorder.start("full")
        path = Path(started["path"])
        self.assertEqual(path.parent, Path(self.temp.name) / "Videos" / "Screen recordings")
        self.assertTrue(path.name.startswith("Recording-") and path.suffix == ".mp4")
        self.assertEqual(stat.S_IMODE(recorder.state_path().stat().st_mode), 0o600)
        running = recorder.status()
        self.assertEqual((running["available"], running["recording"]), (True, True))
        with self.assertRaisesRegex(CommandError, "already running"):
            recorder.start("full")
        stopped = recorder.stop()
        self.assertEqual((stopped["recording"], stopped["name"], stopped["size"]), (False, path.name, len(b"fake video")))
        self.assertFalse(recorder.state_path().exists())
        self.assertFalse(recorder.status()["recording"])
        with self.assertRaisesRegex(CommandError, "No recording"):
            recorder.stop()

    def test_toggle_starts_then_stops_and_files_never_overwrite_each_other(self):
        from datetime import datetime
        stamp = datetime(2026, 10, 15, 12, 0, 0)
        with patch("prismos.recorder.focused_output", return_value=None):
            first = recorder.toggle("full")
            self.assertTrue(first["recording"])
            self.assertEqual(recorder.toggle()["recording"], False)
            second = recorder.start("full", now=stamp)
            recorder.stop()
            third = recorder.start("full", now=stamp)
            recorder.stop()
        self.assertEqual(Path(second["path"]).name, "Recording-2026-10-15-120000.mp4")
        self.assertEqual(Path(third["path"]).name, "Recording-2026-10-15-120000-2.mp4")

    def test_a_stale_state_file_is_cleaned_up(self):
        recorder.write_state(2 ** 22 + 7, "/tmp/x.mp4", 0)
        self.assertIsNone(recorder.read_state())
        self.assertFalse(recorder.state_path().exists())
        # A live process that is not a recorder is never signalled.
        recorder.write_state(os.getpid(), "/tmp/x.mp4", 0)
        self.assertIsNone(recorder.read_state())

    def test_damaged_state_reads_as_not_recording(self):
        recorder.state_path().write_text("{nope")
        self.assertFalse(recorder.status()["recording"])


class LaunchTests(Isolated):
    def start(self, mode="full", **env):
        process = MagicMock(pid=424242)
        process.poll.return_value = None
        with patch("prismos.recorder.subprocess.Popen", return_value=process) as popen, \
                patch("prismos.recorder.time.sleep"), patch("prismos.recorder.alive", return_value=True):
            result = recorder.start(mode)
        return popen.call_args.args[0], result

    def test_full_screen_records_the_focused_output(self):
        with patch("prismos.recorder.focused_output", return_value="DP-1"):
            argv, _ = self.start("full")
        self.assertEqual(argv[:2], ["wf-recorder", "-f"])
        self.assertEqual(argv[argv.index("-o") + 1], "DP-1")
        self.assertNotIn("-g", argv)
        self.assertNotIn("--audio", argv)

    def test_an_area_uses_the_selection_and_rejects_anything_that_is_not_a_region(self):
        with patch("prismos.recorder.shutil.which", return_value="/usr/bin/x"), patch("prismos.recorder.run", return_value="10,20 300x200"):
            argv, _ = self.start("area")
        self.assertEqual(argv[argv.index("-g") + 1], "10,20 300x200")
        for bad in ("; reboot", "10,20 300", "", "a,b cxd"):
            with self.subTest(selection=bad), patch("prismos.recorder.shutil.which", return_value="/usr/bin/x"), \
                    patch("prismos.recorder.run", return_value=bad), self.assertRaisesRegex(ValueError, "cancelled"):
                recorder.start("area")
        with patch("prismos.recorder.shutil.which", return_value="/usr/bin/x"), \
                patch("prismos.recorder.run", side_effect=CommandError("slurp: selection cancelled")), \
                self.assertRaisesRegex(ValueError, "cancelled"):
            recorder.start("area")

    def test_a_window_uses_its_box_from_hyprctl(self):
        with patch("prismos.recorder.run", return_value=json.dumps({"at": [5, 6], "size": [700, 400]})):
            argv, _ = self.start("window")
        self.assertEqual(argv[argv.index("-g") + 1], "5,6 700x400")
        with patch("prismos.recorder.run", return_value=json.dumps({"at": [0, 0], "size": [0, 0]})), \
                self.assertRaisesRegex(ValueError, "No window"):
            recorder.start("window")

    def test_microphone_audio_is_added_only_when_asked_for(self):
        settings.update(record_audio=True)
        with patch("prismos.recorder.focused_output", return_value=None):
            argv, _ = self.start("full")
        self.assertIn("--audio", argv)

    def test_without_hyprctl_the_recorder_picks_its_own_screen(self):
        with patch("prismos.recorder.run", side_effect=CommandError("hyprctl is not installed")):
            self.assertIsNone(recorder.focused_output())
        argv, _ = self.start("full")
        self.assertNotIn("-o", argv)

    def test_an_unusable_output_name_is_refused(self):
        with patch("prismos.recorder.run", return_value=json.dumps([{"name": "bad name; rm", "focused": True}])):
            with self.assertRaises(ValueError):
                recorder.focused_output()
        with patch("prismos.recorder.run", return_value=json.dumps([{"name": "HDMI-A-1", "focused": True}])):
            self.assertEqual(recorder.focused_output(), "HDMI-A-1")

    def test_a_recorder_that_exits_at_once_is_reported_and_leaves_no_state(self):
        process = MagicMock(pid=1)
        process.poll.return_value = 1
        with patch("prismos.recorder.subprocess.Popen", return_value=process), patch("prismos.recorder.time.sleep"), \
                patch("prismos.recorder.focused_output", return_value=None), self.assertRaisesRegex(CommandError, "could not start"):
            recorder.start("full")
        self.assertFalse(recorder.state_path().exists())

    def test_unknown_modes_and_missing_tools_are_refused(self):
        with self.assertRaises(ValueError):
            recorder.start("everything")
        with patch("prismos.recorder.shutil.which", return_value=None):
            self.assertEqual(recorder.status()["available"], False)
            with self.assertRaisesRegex(CommandError, "wf-recorder"):
                recorder.start("full")
        (self.fake / "wf-recorder").chmod(0o755)
        with patch("prismos.recorder.shutil.which", side_effect=lambda name: "/x" if name == "wf-recorder" else None), \
                self.assertRaisesRegex(CommandError, "slurp"):
            recorder.start("area")

    def test_an_empty_file_after_stopping_is_reported(self):
        recorder.write_state(5, str(Path(self.temp.name) / "none.mp4"), 0)
        with patch("prismos.recorder.alive", side_effect=[True, True, False, False]), patch("prismos.recorder.os.kill"), \
                patch("prismos.recorder.time.sleep"), self.assertRaisesRegex(CommandError, "not saved"):
            recorder.stop()

    def test_the_audio_setting_and_cli(self):
        self.assertEqual(self.call(["record", "audio", "yes"])[1]["audio"], True)
        self.assertEqual(self.call(["record", "audio", "no"])[1]["audio"], False)
        self.assertEqual(self.call(["record", "audio", "maybe"])[0], 1)
        self.assertEqual(self.call(["record", "status"])[1]["recording"], False)
        self.assertEqual(self.call(["record", "stop"])[0], 1)


class StatusTests(Isolated):
    def test_elapsed_time_comes_from_the_start_time(self):
        with patch("prismos.recorder.alive", return_value=True):
            recorder.write_state(1234, "/x.mp4", 1000.0)
            self.assertEqual(recorder.status(now=1065.9)["seconds"], 65)
            self.assertEqual(recorder.status(now=900)["seconds"], 0)

    def test_the_tile_and_setting_exist(self):
        from prismos import tiles
        self.assertIn("screen_record", tiles.IDS)
        self.assertIs(settings.load()["record_audio"], False)

    def test_the_recorder_is_a_dependency(self):
        root = Path(__file__).resolve().parent.parent
        self.assertIn("'wf-recorder'", (root / "packaging/arch/PKGBUILD").read_text())
        self.assertIn("wf-recorder", (root / "archiso/packages.x86_64").read_text().split())


if __name__ == "__main__":
    unittest.main()
