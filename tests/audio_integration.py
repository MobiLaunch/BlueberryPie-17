#!/usr/bin/env python3
"""Exercise production audio controls on a private, virtual-only PipeWire server.

Run with: dbus-run-session -- python tests/audio_integration.py
No hardware monitor is started; WirePlumber's policy-only profile manages four
null nodes in an isolated runtime/config/state directory.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from prismos import audio
from prismos.system import CommandError, run


def eventually(read, accept, label, seconds=12):
    deadline = time.monotonic() + seconds
    result = None
    while time.monotonic() < deadline:
        try:
            result = read()
            if accept(result):
                return result
        except CommandError:
            pass
        time.sleep(.1)
    raise AssertionError(f"Timed out waiting for {label}: {result}")


def main():
    for tool in ("pipewire", "wireplumber", "pw-dump", "pw-cli", "wpctl"):
        if not shutil.which(tool):
            raise SystemExit(f"Virtual audio integration requires {tool}")
    if not os.environ.get("DBUS_SESSION_BUS_ADDRESS"):
        raise SystemExit("Run inside dbus-run-session")
    with tempfile.TemporaryDirectory(prefix="prism-audio-test-") as directory:
        folder = Path(directory)
        for name in ("runtime", "config", "state", "cache", "data"):
            path = folder/name; path.mkdir(mode=0o700)
            os.environ["XDG_" + name.upper() + ("_DIR" if name == "runtime" else "_HOME")] = str(path)
        # Private core name + runtime prevent contact with any user's audio server.
        os.environ["PIPEWIRE_REMOTE"] = "prism-audio-test"
        os.environ["PIPEWIRE_RUNTIME_DIR"] = str(folder/"runtime")
        config = folder/"config/pipewire/pipewire.conf.d"
        config.mkdir(parents=True)
        nodes = []
        for name, media in (("speakers", "Audio/Sink"), ("headphones", "Audio/Sink"),
                            ("microphone", "Audio/Source"), ("usb-microphone", "Audio/Source")):
            nodes.append("{ factory = adapter args = { factory.name = support.null-audio-sink "
                "node.name = " + json.dumps("prism-test-" + name) + " node.description = " + json.dumps("Test " + name) +
                " media.class = " + json.dumps(media) + " audio.position = [ FL FR ] } }")
        # context.objects is parsed as SPA-JSON objects: use its native separators.
        (config/"80-prism-test.conf").write_text("context.properties = { core.name = prism-audio-test }\ncontext.objects = [\n" + "\n".join(nodes) + "\n]\n")
        children, logs = [], []
        try:
            for name, command in (("pipewire", ["pipewire"]), ("wireplumber", ["wireplumber", "--profile", "policy"])):
                log = open(folder/(name+".log"), "w+"); logs.append(log)
                children.append(subprocess.Popen(command, stdout=log, stderr=log))
                if name == "pipewire":
                    eventually(lambda: (folder/"runtime/prism-audio-test").exists(), bool, "private core socket")
            devices = eventually(audio.graph, lambda rows: len(rows) == 4, "four virtual endpoints")
            output = next(d for d in devices if d["name"] == "prism-test-speakers")
            microphone = next(d for d in devices if d["name"] == "prism-test-microphone")

            def act(operation, device, value=None):
                return audio.action(operation, device["kind"], device["serial"], device["name"], value)

            eventually(lambda: act("select", output), lambda result: result["ok"], "WirePlumber default-node API")
            act("select", microphone)
            current = eventually(audio.snapshot, lambda data: data.get("output") and data.get("input") and
                data["output"]["name"] == output["name"] and data["input"]["name"] == microphone["name"], "selected defaults")
            act("volume", output, "35")
            act("mute", output, "1")
            act("volume", microphone, "62")
            act("mute", microphone, "1")
            current = eventually(audio.snapshot, lambda data: data.get("output") and data.get("input") and
                data["output"]["value"] == 35 and data["output"]["muted"] and
                data["input"]["value"] == 62 and data["input"]["muted"], "volume and mute readback")
            act("mute", microphone, "0")
            eventually(audio.snapshot, lambda data: data.get("input") and not data["input"]["muted"] and
                       data["output"]["muted"], "independent microphone unmute")
            headphones = next(d for d in devices if d["name"] == "prism-test-headphones")
            act("select", headphones)
            eventually(audio.snapshot, lambda data: data.get("output") and data["output"]["name"] == headphones["name"], "output switching")
            run(["pw-cli", "destroy", str(headphones["id"])])
            eventually(audio.graph, lambda rows: not any(d["serial"] == headphones["serial"] for d in rows), "virtual device removal")
            try:
                act("select", headphones)
            except CommandError:
                pass
            else:
                raise AssertionError("Removed endpoint was accepted")
            print("PASS: real PipeWire/WirePlumber discovery, defaults, volume, mute, microphone isolation and removed-device rejection on virtual endpoints")
        except Exception:
            for log in logs:
                log.flush(); log.seek(0)
                print(log.read()[-4000:])
            raise
        finally:
            for child in reversed(children):
                child.terminate()
                try:
                    child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait()
            for log in logs: log.close()


if __name__ == "__main__": main()
