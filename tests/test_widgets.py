import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prismos import cli, settings, stats, weather, widgets


class StatsTests(unittest.TestCase):
    def test_cpu_memory_and_storage_from_proc_style_files(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = "cpu  100 0 100 700 100 0 0 0 0 0\n"
            second = "cpu  200 0 200 750 150 0 0 0 0 0\n"
            (root / "stat").write_text(first)
            def advance(_):
                (root / "stat").write_text(second)
            with patch("prismos.stats.time.sleep", side_effect=advance):
                self.assertEqual(stats.cpu_percent(0.0, root / "stat"), 67)  # 200 busy of 300
            (root / "meminfo").write_text("MemTotal: 16777216 kB\nMemAvailable: 4194304 kB\n")
            self.assertEqual(stats.memory(root / "meminfo"), {"used_gib": 12.0, "total_gib": 16.0, "percent": 75})

    def test_missing_files_give_none_not_a_crash(self):
        self.assertIsNone(stats.cpu_percent(0, "/nonexistent"))
        self.assertIsNone(stats.memory("/nonexistent"))
        self.assertTrue(stats.snapshot("/nonexistent", "/nonexistent", 0)["ok"])


class WeatherTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        env = patch.dict(os.environ, {"XDG_CONFIG_HOME": temp.name + "/c", "XDG_CACHE_HOME": temp.name + "/k", "HOME": temp.name})
        env.start(); self.addCleanup(env.stop)
        self.calls = []

    def reply(self, payload):
        def fake(url):
            self.calls.append(url)
            return json.dumps(payload).encode()
        return patch("prismos.weather.fetch", side_effect=fake)

    FORECAST = {"current": {"temperature_2m": 17.6, "apparent_temperature": 16.2, "weather_code": 2, "is_day": 1},
                "daily": {"temperature_2m_max": [20.1], "temperature_2m_min": [11.4]}}

    def test_nothing_is_requested_until_a_place_is_chosen(self):
        with self.reply(self.FORECAST):
            self.assertEqual(weather.current(), {"ok": True, "configured": False})
        self.assertEqual(self.calls, [])

    def test_current_conditions_are_parsed_and_cached_for_fifteen_minutes(self):
        weather.choose(48.8566, 2.3522, "Paris, France")
        with self.reply(self.FORECAST):
            first = weather.current(now=1000)
            again = weather.current(now=1000 + 600)
            later = weather.current(now=1000 + 1000)
        self.assertEqual((first["temperature"], first["high"], first["low"], first["icon"]), (18, 20, 11, "partly_cloudy"))
        self.assertTrue(again["cached"])
        self.assertEqual(len(self.calls), 2)  # initial + after the cache expired
        self.assertIn("latitude=48.8566", self.calls[0])
        self.assertTrue(self.calls[0].startswith(weather.FORECAST))

    def test_clear_night_uses_the_moon(self):
        weather.choose(10, 10, "Somewhere")
        night = {"current": dict(self.FORECAST["current"], weather_code=0, is_day=0), "daily": self.FORECAST["daily"]}
        with self.reply(night):
            self.assertEqual(weather.current(now=1)["icon"], "moon")

    def test_network_failure_is_reported_without_crashing(self):
        weather.choose(10, 10, "Somewhere")
        with patch("prismos.weather.fetch", side_effect=OSError("offline")):
            result = weather.current(now=1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["label"], "Somewhere")

    def test_place_search_validates_results(self):
        payload = {"results": [{"name": "Paris", "admin1": "Île-de-France", "country": "France", "latitude": 48.85, "longitude": 2.35},
                               {"name": "Bad", "latitude": 999, "longitude": 0}, {"name": "Missing"}]}
        with self.reply(payload):
            result = weather.search("Paris")
        self.assertEqual([p["label"] for p in result["places"]], ["Paris, Île-de-France, France"])
        with self.assertRaises(ValueError):
            weather.search("x")

    def test_choose_rejects_bad_coordinates_labels_and_units(self):
        for args in ((91, 0, "x"), (0, 181, "x"), ("nan", 0, "x"), (0, 0, ""), (0, 0, "a\x00b"), (0, 0, "x", "kelvin")):
            with self.subTest(args=args), self.assertRaises(ValueError):
                weather.choose(*args)
        self.assertEqual(settings.load()["weather"], {})

    def test_fetch_only_talks_to_the_two_fixed_https_hosts(self):
        for url in ("http://api.open-meteo.com/v1/forecast", "https://evil.example/v1/forecast",
                    "https://api.open-meteo.com.evil.example/x", "file:///etc/passwd"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                weather.fetch(url)

    def test_disable_forgets_the_place(self):
        weather.choose(10, 10, "Somewhere")
        weather.disable()
        self.assertEqual(weather.current(), {"ok": True, "configured": False})


class WidgetTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        env = patch.dict(os.environ, {"XDG_CONFIG_HOME": temp.name}); env.start(); self.addCleanup(env.stop)

    def test_defaults_then_user_choice_in_catalog_order(self):
        self.assertEqual(widgets.enabled(), ["glance", "clock", "search", "calendar", "media"])
        widgets.change(["system", "clock", "clock"])
        self.assertEqual(widgets.enabled(), ["clock", "system"])
        widgets.change([])
        self.assertEqual(widgets.enabled(), [])

    def test_unknown_widgets_are_rejected(self):
        with self.assertRaises(ValueError):
            widgets.change(["clock", "../../etc"])
        self.assertEqual(widgets.enabled(), ["glance", "clock", "search", "calendar", "media"])

    def test_hostile_saved_values_are_filtered(self):
        settings.directory().mkdir(parents=True, exist_ok=True)
        (settings.directory() / "settings.json").write_text(json.dumps({"widgets": ["clock", "bogus", 4], "weather": {"lat": "x"}}))
        self.assertEqual(widgets.enabled(), ["clock"])
        self.assertEqual(settings.load()["weather"], {})

    def test_cli(self):
        for argv in (["widgets", "set", "calendar", "weather"], ["widgets", "list"], ["stats"]):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(cli.main(argv), 0, argv)
            self.assertTrue(json.loads(out.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()


class WebSearchTests(unittest.TestCase):
    @patch("prismos.websearch.subprocess.Popen")
    def test_query_is_url_encoded_into_a_fixed_https_url(self, popen):
        from prismos import websearch
        result = websearch.search("c++ & rust #1")
        self.assertEqual(result["url"], "https://duckduckgo.com/?q=c%2B%2B+%26+rust+%231")
        popen.assert_called_once()
        self.assertEqual(popen.call_args.args[0][0], "xdg-open")

    @patch("prismos.websearch.subprocess.Popen")
    def test_empty_oversized_and_control_characters_are_refused(self, popen):
        from prismos import websearch
        for query in ("", "   ", "x" * 201, "a\x00b", None):
            with self.subTest(query=query), self.assertRaises(ValueError):
                websearch.search(query)
        popen.assert_not_called()


class WidgetSizeTests(unittest.TestCase):
    def setUp(self):
        import contextlib, io, json, os, tempfile
        from unittest.mock import patch
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.contextlib, self.io, self.json = contextlib, io, json

    def call(self, argv):
        from prismos import cli
        with self.contextlib.redirect_stdout(self.io.StringIO()) as out:
            code = cli.main(argv)
        return code, self.json.loads(out.getvalue())

    def test_sizes_persist_for_resizable_widgets_only(self):
        from prismos import settings
        code, result = self.call(["widgets", "size", "notes", "large"])
        self.assertEqual((code, result["sizes"]), (0, {"notes": "large"}))
        self.call(["widgets", "size", "system", "small"])
        self.assertEqual(settings.load()["widget_sizes"], {"notes": "large", "system": "small"})
        self.assertEqual(self.call(["widgets", "list"])[1]["resizable"], ["calendar", "weather", "system", "notes"])
        for bad in (["clock", "large"], ["notes", "huge"], ["notes"], ["../x", "small"], ["notes", "large", "extra"]):
            self.assertEqual(self.call(["widgets", "size", *bad])[0], 1, bad)
        self.assertEqual(settings.load()["widget_sizes"], {"notes": "large", "system": "small"})

    def test_corrupt_sizes_are_filtered(self):
        from prismos import settings
        settings.directory().mkdir()
        (settings.directory() / "settings.json").write_text(self.json.dumps({"widget_sizes": {"notes": "large", "clock": "large", "system": "gigantic", "../x": "small"}}))
        self.assertEqual(settings.load()["widget_sizes"], {"notes": "large"})
