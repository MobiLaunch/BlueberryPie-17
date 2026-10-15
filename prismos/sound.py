"""Short alert sounds from the freedesktop sound theme. Only two fixed files can play."""
import shutil
import subprocess
from pathlib import Path

from .system import CommandError

SOUNDS = {
    "alarm": "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga",
    "ding": "/usr/share/sounds/freedesktop/stereo/complete.oga",
}
PLAYERS = (["pw-play"], ["paplay"])


def play(name):
    if name not in SOUNDS:
        raise ValueError("Unknown sound")
    path = Path(SOUNDS[name])
    if not path.is_file():
        raise CommandError("The sound theme is not installed")
    player = next((cmd for cmd in PLAYERS if shutil.which(cmd[0])), None)
    if player is None:
        raise CommandError("No audio player (pw-play or paplay) was found")
    subprocess.Popen([*player, str(path)], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    return {"ok": True, "sound": name}
