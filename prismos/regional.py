"""Fixed region, language and keyboard choices shared by Settings and the installer.

Everything here is an allowlist: a value from the UI is accepted only if it is
listed (or, for time zones, present in the system tz database), so none of it can
carry text into a file or command that was not anticipated.
"""
import os
from pathlib import Path

# (locale, label). Latin-script locales only: the shell fonts do not ship CJK glyphs.
LOCALES = (
    ("en_US.UTF-8", "English (United States)"),
    ("en_GB.UTF-8", "English (United Kingdom)"),
    ("de_DE.UTF-8", "Deutsch"),
    ("fr_FR.UTF-8", "Français"),
    ("es_ES.UTF-8", "Español"),
    ("it_IT.UTF-8", "Italiano"),
    ("pt_PT.UTF-8", "Português (Portugal)"),
    ("pt_BR.UTF-8", "Português (Brasil)"),
    ("nl_NL.UTF-8", "Nederlands"),
    ("pl_PL.UTF-8", "Polski"),
    ("sv_SE.UTF-8", "Svenska"),
    ("tr_TR.UTF-8", "Türkçe"),
)

# (id, label, linux console keymap, XKB layout, XKB variant)
KEYBOARDS = (
    ("us", "English (US)", "us", "us", ""),
    ("gb", "English (UK)", "uk", "gb", ""),
    ("de", "German", "de-latin1", "de", ""),
    ("fr", "French", "fr", "fr", ""),
    ("es", "Spanish", "es", "es", ""),
    ("it", "Italian", "it", "it", ""),
    ("pt", "Portuguese", "pt-latin1", "pt", ""),
    ("br", "Portuguese (Brazil)", "br-abnt2", "br", ""),
    ("nl", "Dutch", "nl", "nl", ""),
    ("pl", "Polish", "pl2", "pl", ""),
    ("se", "Swedish", "sv-latin1", "se", ""),
    ("tr", "Turkish", "trq", "tr", ""),
    ("dvorak", "English (Dvorak)", "dvorak", "us", "dvorak"),
    ("colemak", "English (Colemak)", "colemak", "us", "colemak"),
)

KEYBOARD_IDS = tuple(item[0] for item in KEYBOARDS)
LOCALE_IDS = tuple(item[0] for item in LOCALES)
ZONEINFO = Path(os.environ.get("PRISM_ZONEINFO", "/usr/share/zoneinfo"))
_SKIP = ("posix", "right", "Etc", "SystemV", "US", "Brazil", "Canada", "Chile", "Mexico")


def keyboard(identifier):
    for item in KEYBOARDS:
        if item[0] == identifier:
            return {"id": item[0], "label": item[1], "console": item[2], "layout": item[3], "variant": item[4]}
    raise ValueError("Unknown keyboard layout")


def timezones():
    """Region/City names from the system tz database, plus UTC; sorted."""
    names = {"UTC"}
    try:
        from zoneinfo import available_timezones
        found = available_timezones()
    except Exception:  # missing tzdata; the installer then offers UTC only
        found = set()
    for name in found:
        head = name.split("/", 1)[0]
        if "/" in name and head not in _SKIP and not name.startswith(("posix/", "right/")):
            names.add(name)
    return sorted(names)


def default_timezone():
    try:
        target = os.readlink("/etc/localtime")
        if "zoneinfo/" in target:
            name = target.split("zoneinfo/", 1)[1]
            if name in timezones():
                return name
    except OSError:
        pass
    return "UTC"
