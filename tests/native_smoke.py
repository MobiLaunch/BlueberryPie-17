#!/usr/bin/env python3
"""Load real Quickshell components offscreen, without hardware writes."""
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    for tool in ("qs", "dbus-run-session"):
        if not shutil.which(tool):
            raise SystemExit(f"Native smoke check requires {tool}")
    with tempfile.TemporaryDirectory(prefix="prism-native-smoke-") as folder:
        root = Path(folder)
        config = root/"config/prismos"; config.mkdir(parents=True)
        (config/"settings.json").write_text(json.dumps({"favorites":["fixture.desktop"], "reduced_motion":True}))
        data = root/"data/applications"; data.mkdir(parents=True)
        (data/"fixture.desktop").write_text("[Desktop Entry]\nType=Application\nName=Fixture\nExec=true\n")
        runtime = root/"runtime"; runtime.mkdir(mode=0o700)
        # Quickshell scans only inside its config root. Keep the fixture and
        # shared modules together, as they are in the installed shell.
        shell = root/"shell"
        shutil.copytree(ROOT/"shell", shell)
        shutil.copytree(ROOT/"design", root/"design")
        fixture = shell/"smoke.qml"
        fixture.write_text((ROOT/"tests/native-smoke.qml").read_text()
                           .replace('"../shell/components"', '"components"')
                           .replace('"../shell/services"', '"services"'))
        env = {**os.environ, "PATH":str(ROOT/"bin")+":"+os.environ["PATH"],
               "XDG_CONFIG_HOME":str(root/"config"), "XDG_DATA_HOME":str(root/"data"),
               "XDG_DATA_DIRS":str(root/"empty-data"), "XDG_CACHE_HOME":str(root/"cache"),
               "XDG_STATE_HOME":str(root/"state"), "XDG_RUNTIME_DIR":str(runtime),
               "QT_QPA_PLATFORM":"offscreen", "QT_QUICK_BACKEND":"software"}
        result = subprocess.run(["dbus-run-session","--","qs","-p",str(fixture)],
                                env=env, capture_output=True, text=True, timeout=20)
        log = result.stdout+result.stderr
        if result.returncode or "PRISM_NATIVE_SMOKE_OK" not in log or re.search(r"ReferenceError|TypeError|Cannot assign|Binding loop detected|PRISM_NATIVE_SMOKE_FAILED", log):
            print(log)
            raise SystemExit("Native component runtime check failed")
        print("PASS: real Quickshell sound/wireless panels, slider binding/drag refresh, private stdin, launch readiness, favorites, media and notifications load offscreen")


if __name__ == "__main__":main()
