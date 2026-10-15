"""PrismOS disk installer engine.

Two halves share this module:

* the unprivileged half lists disks, validates a request and previews exactly what
  would happen (`prismctl installer ...`), and hands the request to
* the root half (`bin/prism-installer-helper`, reached only through polkit), which
  re-validates everything itself and then executes a fixed list of steps.

Safety rules, in the order they matter:

1. Nothing destructive runs unless the request names an eligible whole disk *and*
   the user typed that disk's name back (`confirm`).
2. Disks that are mounted, read-only, too small, or look like the live USB are never
   eligible. The root half repeats this check against a fresh `lsblk`.
3. Every command is an argv list; no request text is ever interpolated into a shell
   line. Request fields are matched against strict patterns or allowlists first.
4. The password travels on stdin only and never appears in argv, previews or logs.
5. The root half refuses to run outside the live medium.

Nothing here has been run against a real disk by the authors; see docs/INSTALLER.md
and docs/VALIDATION.md for what was and was not exercised.
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import threading
from collections import deque
from pathlib import Path

from . import regional
from .system import CommandError, run

HELPER = "/usr/libexec/prism-installer-helper"
LIVE_MARKER = Path("/run/archiso")
WORK = Path("/run/prismos-install")
TARGET = WORK / "target"
OFFLINE_REPO = Path("/opt/prismos/repo")
PACMAN_CONF = Path("/etc/pacman.conf")
NM_CONNECTIONS = Path("/etc/NetworkManager/system-connections")
EFI_DIR = Path("/sys/firmware/efi")
GIB = 1024 ** 3
MIN_DISK = 16 * GIB
ESP_MIB = 1024
SAFE_PATH = "/usr/local/sbin:/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin"

DISK_PATH = re.compile(r"/dev/[A-Za-z0-9][A-Za-z0-9._-]{0,30}\Z")
IGNORED_DEVICES = re.compile(r"/dev/(loop|ram|zram|sr|fd|nbd)[0-9]*\Z")
HOSTNAME = re.compile(r"(?!-)[a-z0-9-]{1,63}(?<!-)\Z")
USERNAME = re.compile(r"[a-z_][a-z0-9_-]{0,31}\Z")
FULL_NAME = re.compile(r"[^\x00-\x1f\x7f:,=]{0,64}\Z")
PASSWORD = re.compile(r"[^\x00-\x1f\x7f]{8,128}\Z")
RESERVED_USERS = {"root", "daemon", "bin", "sys", "sync", "games", "man", "mail", "ftp", "http",
                  "nobody", "greeter", "dbus", "polkitd", "avahi", "uuidd", "git", "ntp"}

# Installed with pacstrap. The prism-shell package pulls in the rest of the desktop.
BASE_PACKAGES = ("base", "linux", "linux-firmware", "grub", "networkmanager", "sudo", "nano",
                 "mesa", "vulkan-intel", "vulkan-radeon", "zram-generator",
                 "greetd", "greetd-tuigreet", "prism-shell", "firefox", "noto-fonts")
SERVICES = ("NetworkManager.service", "bluetooth.service", "greetd.service", "systemd-timesyncd.service")
HYPR_FILES = ("hyprland.lua", "hyprlock.conf", "hypridle.conf")


# ----------------------------------------------------------------------------
# Facts about the machine
# ----------------------------------------------------------------------------

def live():
    return LIVE_MARKER.is_dir()


def firmware():
    return "uefi" if EFI_DIR.is_dir() else "bios"


def microcode():
    try:
        text = Path("/proc/cpuinfo").read_text()
    except OSError:
        return None
    if "GenuineIntel" in text:
        return "intel-ucode"
    if "AuthenticAMD" in text:
        return "amd-ucode"
    return None


def human(size):
    if size >= 1000 ** 4:
        return f"{size / 1000 ** 4:.1f} TB".replace(".0 ", " ")
    return f"{round(size / 1000 ** 3)} GB"


def connectivity():
    try:
        state = run(["nmcli", "-t", "-g", "CONNECTIVITY", "general"], timeout=6)
    except CommandError:
        return "unknown"
    return state if state in ("full", "limited", "portal", "none") else "unknown"


def status():
    from . import system
    state = connectivity()
    return {"ok": True, "live": live(), "firmware": firmware(), "connectivity": state,
            "online": state in ("full", "limited"), "battery": system.battery(),
            "min_disk": MIN_DISK, "min_disk_label": human(MIN_DISK)}


def options():
    return {"ok": True,
            "locales": [{"id": key, "label": label} for key, label in regional.LOCALES],
            "keyboards": [{"id": item[0], "label": item[1]} for item in regional.KEYBOARDS],
            "timezones": regional.timezones(), "default_timezone": regional.default_timezone()}


# ----------------------------------------------------------------------------
# Disks
# ----------------------------------------------------------------------------

def _mounts(node):
    values = node.get("mountpoints")
    if values is None:
        values = [node.get("mountpoint")]
    found = [value for value in values if isinstance(value, str) and value]
    for child in node.get("children") or []:
        found += _mounts(child)
    return found


def _descendants(node):
    for child in node.get("children") or []:
        yield child
        yield from _descendants(child)


def classify(node):
    """Return (eligible, reason) for one top-level lsblk node."""
    reasons = []
    mounts = [m for m in _mounts(node) if not str(m).startswith(str(WORK))]  # a stale installer mount is ours
    nodes = [node, *_descendants(node)]
    labels = {str(item.get("label") or "") for item in nodes}
    types = {str(item.get("fstype") or "") for item in nodes}
    if any(m.startswith("/run/archiso") for m in mounts) or "iso9660" in types \
            or any(label.startswith(("PRISM_", "ARCHISO")) for label in labels):
        return False, "This is the USB you started from"
    if mounts:
        return False, "In use; unmount it first"
    if node.get("ro") in (True, 1, "1"):
        return False, "Read-only"
    if int(node.get("size") or 0) < MIN_DISK:
        return False, f"Smaller than {human(MIN_DISK)}"
    return True, ""


def disks(tree=None):
    if tree is None:
        columns = "NAME,PATH,SIZE,TYPE,MODEL,TRAN,RO,RM,MOUNTPOINTS,FSTYPE,LABEL"
        try:
            tree = json.loads(run(["lsblk", "--json", "--bytes", "--paths", "--output", columns], timeout=10))
        except (ValueError, TypeError) as error:
            raise CommandError("Could not read the list of disks") from error
    result = []
    for node in tree.get("blockdevices", []) if isinstance(tree, dict) else []:
        path = str(node.get("path") or node.get("name") or "")
        if node.get("type") != "disk" or not DISK_PATH.fullmatch(path) or IGNORED_DEVICES.fullmatch(path):
            continue
        eligible, reason = classify(node)
        size = int(node.get("size") or 0)
        result.append({
            "path": path, "name": path.rsplit("/", 1)[-1], "size": size, "size_label": human(size),
            "model": str(node.get("model") or "").strip()[:40] or "Disk",
            "transport": str(node.get("tran") or "").upper(),
            "removable": node.get("rm") in (True, 1, "1"),
            "partitions": [{"path": str(part.get("path") or ""), "size_label": human(int(part.get("size") or 0)),
                            "fstype": str(part.get("fstype") or ""), "label": str(part.get("label") or "")}
                           for part in node.get("children") or [] if part.get("type") == "part"],
            "eligible": eligible, "reason": reason})
    return sorted(result, key=lambda disk: (not disk["eligible"], disk["path"]))


def disk_listing():
    return {"ok": True, "disks": disks()}


# ----------------------------------------------------------------------------
# Requests
# ----------------------------------------------------------------------------

def validate(data, available=None):
    """Normalize an untrusted request or raise ValueError with a message safe to show."""
    if not isinstance(data, dict):
        raise ValueError("The installation request is not valid")
    disk_path = data.get("disk")
    if not isinstance(disk_path, str) or not DISK_PATH.fullmatch(disk_path):
        raise ValueError("Choose a disk to install to")
    listed = {disk["path"]: disk for disk in (available if available is not None else disks())}
    disk = listed.get(disk_path)
    if disk is None:
        raise ValueError("That disk is no longer available")
    if not disk["eligible"]:
        raise ValueError(f"{disk['name']} cannot be used: {disk['reason'] or 'not eligible'}")
    if data.get("confirm") != disk["name"]:
        raise ValueError(f"Type {disk['name']} to confirm erasing the disk")
    hostname = str(data.get("hostname") or "").strip().lower()
    if not HOSTNAME.fullmatch(hostname):
        raise ValueError("The computer name may use letters, numbers and hyphens")
    username = str(data.get("username") or "").strip()
    if not USERNAME.fullmatch(username) or username in RESERVED_USERS or username.startswith("systemd-"):
        raise ValueError("Choose a different user name (lowercase letters, numbers, - and _)")
    fullname = str(data.get("fullname") or "").strip()
    if not FULL_NAME.fullmatch(fullname):
        raise ValueError("The name may not contain colons, commas or control characters")
    password = data.get("password")
    if not isinstance(password, str) or not PASSWORD.fullmatch(password):
        raise ValueError("The password must be 8 to 128 characters")
    timezone = data.get("timezone")
    if timezone not in regional.timezones():
        raise ValueError("Choose a time zone from the list")
    locale = data.get("locale")
    if locale not in regional.LOCALE_IDS:
        raise ValueError("Choose a language from the list")
    keyboard = regional.keyboard(data.get("keyboard")) if data.get("keyboard") in regional.KEYBOARD_IDS else None
    if keyboard is None:
        raise ValueError("Choose a keyboard layout from the list")
    return {"disk": disk_path, "disk_name": disk["name"], "disk_size": disk["size_label"],
            "hostname": hostname, "username": username, "fullname": fullname, "password": password,
            "timezone": timezone, "locale": locale, "keyboard": keyboard}


def partition_path(disk, number):
    return f"{disk}{'p' if disk[-1].isdigit() else ''}{number}"


def layout(disk, mode):
    """Partition table for a whole-disk install; GPT in both firmware modes."""
    if mode == "uefi":
        return {"boot": partition_path(disk, 1), "root": partition_path(disk, 2),
                "parts": [("EFI system partition", f"{ESP_MIB // 1024} GB, FAT32"),
                          ("PrismOS", "the rest of the disk, ext4")]}
    return {"boot": partition_path(disk, 1), "root": partition_path(disk, 2),
            "parts": [("BIOS boot area", "1 MB"), ("PrismOS", "the rest of the disk, ext4")]}


# ----------------------------------------------------------------------------
# The plan: a fixed, ordered list of steps
# ----------------------------------------------------------------------------

def _step(phase, label, kind="run", weight=1, optional=False, **fields):
    return {"phase": phase, "label": label, "kind": kind, "weight": weight, "optional": optional, **fields}


def _chroot(*argv):
    return ["arch-chroot", str(TARGET), *argv]


def _write(path, text, mode=0o644):
    return {"path": path, "text": text, "mode": mode}


def steps(plan, mode, ucode=None):
    disk, user, host = plan["disk"], plan["username"], plan["hostname"]
    parts = layout(disk, mode)
    home = f"/home/{user}"
    config = f"{home}/.config/prismos"
    packages = list(BASE_PACKAGES) + ([ucode] if ucode else []) + (["efibootmgr"] if mode == "uefi" else [])
    locales = dict.fromkeys([plan["locale"], "en_US.UTF-8"])
    uefi_flags = ["--target=x86_64-efi", "--efi-directory=/boot"]
    if mode == "uefi":
        table = ["--new=1:0:+%dM" % ESP_MIB, "--typecode=1:ef00", "--change-name=1:EFI",
                 "--new=2:0:0", "--typecode=2:8304", "--change-name=2:PrismOS"]
    else:
        table = ["--new=1:0:+1M", "--typecode=1:ef02", "--change-name=1:BIOS",
                 "--new=2:0:0", "--typecode=2:8304", "--change-name=2:PrismOS"]
    result = [
        _step("prepare", "Getting ready", argv=["umount", "-R", str(TARGET)], optional=True),
        _step("partition", "Erasing the disk", argv=["wipefs", "--all", "--force", disk]),
        _step("partition", "Creating partitions", argv=["sgdisk", "--zap-all", disk]),
        _step("partition", "Creating partitions", argv=["sgdisk", *table, disk]),
        _step("partition", "Creating partitions", argv=["udevadm", "settle", "--timeout=30"]),
        _step("partition", "Creating partitions", kind="wait", paths=[parts["boot"], parts["root"]]),
        _step("format", "Formatting", argv=["mkfs.ext4", "-F", "-L", "prismos", parts["root"]]),
    ]
    if mode == "uefi":
        result.append(_step("format", "Formatting", argv=["mkfs.fat", "-F", "32", "-n", "PRISMEFI", parts["boot"]]))
    result += [
        _step("mount", "Preparing the new system", kind="mkdir", path=str(TARGET)),
        _step("mount", "Preparing the new system", argv=["mount", parts["root"], str(TARGET)]),
    ]
    if mode == "uefi":
        result += [_step("mount", "Preparing the new system", kind="mkdir", path=str(TARGET / "boot")),
                   _step("mount", "Preparing the new system", argv=["mount", parts["boot"], str(TARGET / "boot")])]
    result += [
        _step("packages", "Installing PrismOS", kind="pacman-conf", weight=0),
        _step("packages", "Downloading and installing PrismOS", weight=60, stream=True, timeout=3600,
              argv=["pacstrap", "-K", "-C", str(WORK / "pacman.conf"), str(TARGET), *packages]),
        _step("configure", "Saving your settings", kind="fstab"),
        _step("configure", "Saving your settings", kind="write", **_write("/etc/hostname", host + "\n")),
        _step("configure", "Saving your settings", kind="write", **_write(
            "/etc/hosts", f"127.0.0.1\tlocalhost\n::1\t\tlocalhost\n127.0.1.1\t{host}.localdomain\t{host}\n")),
        _step("configure", "Saving your settings", kind="write", **_write(
            "/etc/locale.gen", "".join(f"{name} UTF-8\n" for name in locales))),
        _step("configure", "Saving your settings", kind="write", **_write("/etc/locale.conf", f"LANG={plan['locale']}\n")),
        _step("configure", "Saving your settings", kind="write", **_write(
            "/etc/vconsole.conf", f"KEYMAP={plan['keyboard']['console']}\n")),
        _step("configure", "Saving your settings", kind="link", path="/etc/localtime",
              target=f"/usr/share/zoneinfo/{plan['timezone']}"),
        _step("configure", "Saving your settings", argv=_chroot("locale-gen")),
        _step("configure", "Saving your settings", argv=_chroot("hwclock", "--systohc"), optional=True),
        _step("configure", "Saving your settings", kind="write", **_write(
            "/etc/sudoers.d/10-wheel", "%wheel ALL=(ALL:ALL) ALL\n", 0o440)),
        _step("configure", "Saving your settings", kind="write", **_write(
            "/etc/greetd/config.toml",
            '[terminal]\nvt = 1\n\n[default_session]\ncommand = "tuigreet --time --remember --cmd prism-session"\n'
            'user = "greeter"\n')),
        _step("configure", "Saving your settings", kind="write", **_write(
            "/etc/systemd/zram-generator.conf", "[zram0]\nzram-size = min(ram / 2, 4096)\ncompression-algorithm = zstd\n")),
        _step("configure", "Saving your settings", kind="copy-connections"),
        _step("account", "Creating your account", argv=_chroot(
            "useradd", "--create-home", "--groups", "wheel,audio,video,input", "--shell", "/bin/bash",
            *(["--comment", plan["fullname"]] if plan["fullname"] else []), user)),
        _step("account", "Creating your account", argv=_chroot("chpasswd"), secret=f"{user}:{plan['password']}\n"),
        _step("account", "Creating your account", argv=_chroot("passwd", "--lock", "root")),
        _step("account", "Creating your account", argv=_chroot(
            "install", "-d", "-m", "700", "-o", user, "-g", user,
            f"{home}/.config", config, f"{config}/hypr")),
    ]
    for name in HYPR_FILES:
        result.append(_step("account", "Creating your account", argv=_chroot(
            "install", "-m", "600", "-o", user, "-g", user,
            f"/usr/share/prismos/config/hypr/{name}", f"{config}/hypr/{name}")))
    result += [
        _step("account", "Creating your account", kind="write", **_write(
            f"{config}/settings.json", json.dumps({"keyboard": plan["keyboard"]["id"]}) + "\n", 0o600)),
        _step("account", "Creating your account", argv=_chroot("chown", f"{user}:{user}", f"{config}/settings.json")),
        _step("services", "Turning on services", argv=_chroot("systemctl", "enable", *SERVICES)),
    ]
    if mode == "uefi":
        result += [
            _step("bootloader", "Setting up startup", argv=_chroot(
                "grub-install", *uefi_flags, "--bootloader-id=PrismOS"), optional=True),
            _step("bootloader", "Setting up startup", argv=_chroot("grub-install", *uefi_flags, "--removable")),
        ]
    else:
        result.append(_step("bootloader", "Setting up startup", argv=_chroot("grub-install", "--target=i386-pc", disk)))
    result += [
        _step("bootloader", "Setting up startup", argv=_chroot("grub-mkconfig", "-o", "/boot/grub/grub.cfg")),
        _step("finish", "Finishing up", argv=["sync"]),
        _step("finish", "Finishing up", argv=["umount", "-R", str(TARGET)]),
    ]
    return result


def preview(data, available=None):
    """What would happen, for the Review page. Never includes the password."""
    plan = validate(data, available)
    mode = firmware()
    parts = layout(plan["disk"], mode)
    shown = []
    for step in steps(plan, mode, microcode()):
        if "argv" in step:
            command = shlex.join(step["argv"])
        elif step["kind"] == "write":
            command = f"write {step['path']}"
        else:
            command = step["kind"] + (f" {step['path']}" if "path" in step else "")
        if step.get("secret"):
            command += "  (password supplied privately)"
        shown.append({"phase": step["phase"], "label": step["label"], "command": command})
    return {"ok": True, "disk": plan["disk"], "disk_name": plan["disk_name"], "disk_size": plan["disk_size"],
            "firmware": mode, "partitions": [{"name": name, "detail": detail} for name, detail in parts["parts"]],
            "hostname": plan["hostname"], "username": plan["username"], "timezone": plan["timezone"],
            "locale": plan["locale"], "keyboard": plan["keyboard"]["label"], "steps": shown}


# ----------------------------------------------------------------------------
# Execution (root half)
# ----------------------------------------------------------------------------

def emit(**event):
    print(json.dumps({"ok": True, **event}), flush=True)


class Host:
    """The real effects. Tests substitute a recorder with the same methods."""

    def run(self, argv, stdin=None, timeout=900, on_line=None):
        env = {"PATH": SAFE_PATH, "LC_ALL": "C", "HOME": "/root"}
        process = subprocess.Popen(argv, stdin=subprocess.PIPE if stdin is not None else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
        timer = threading.Timer(timeout, process.kill)
        timer.start()
        tail = deque(maxlen=12)
        try:
            if stdin is not None:
                process.stdin.write(stdin)
                process.stdin.close()
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    tail.append(line)
                    if on_line:
                        on_line(line)
            code = process.wait()
        finally:
            timer.cancel()
        if code:
            raise CommandError(" / ".join(tail)[-400:] or f"{argv[0]} failed ({code})")
        return "\n".join(tail)

    def capture(self, argv):
        return run(argv, timeout=120)

    def inside(self, path):
        full = (TARGET / str(path).lstrip("/"))
        if os.path.commonpath([os.path.realpath(TARGET), os.path.realpath(full.parent)]) != os.path.realpath(TARGET):
            raise CommandError("Refused to write outside the new system")
        return full

    def write(self, path, text, mode):
        full = self.inside(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(full, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, mode)
        with os.fdopen(fd, "w") as stream:
            stream.write(text)
        os.chmod(full, mode)

    def link(self, path, target):
        full = self.inside(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        if full.is_symlink() or full.exists():
            full.unlink()
        os.symlink(target, full)

    def mkdir(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)

    def wait_for(self, paths, seconds=30):
        import time
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if all(Path(path).exists() for path in paths):
                return
            time.sleep(0.5)
        raise CommandError("The new partitions did not appear")

    def pacman_conf(self):
        WORK.mkdir(parents=True, exist_ok=True)
        source = PACMAN_CONF.read_text()
        kept, skipping = [], False
        for line in source.splitlines():
            if line.strip().startswith("["):
                skipping = line.strip() == "[prismos]"
            if not skipping:
                kept.append(line)
        if OFFLINE_REPO.is_dir():
            kept += ["", "[prismos]", "SigLevel = Optional TrustAll", f"Server = file://{OFFLINE_REPO}"]
        (WORK / "pacman.conf").write_text("\n".join(kept) + "\n")

    def copy_connections(self):
        source = NM_CONNECTIONS
        if not source.is_dir():
            return
        destination = self.inside("/etc/NetworkManager/system-connections/x").parent
        destination.mkdir(parents=True, exist_ok=True)
        os.chmod(destination, 0o700)
        for item in source.glob("*.nmconnection"):
            if item.is_file() and not item.is_symlink():
                target = destination / item.name
                shutil.copyfile(item, target)
                os.chmod(target, 0o600)


def execute(plan_steps, host, report=emit):
    total = sum(step["weight"] for step in plan_steps) or 1
    done = 0
    for step in plan_steps:
        percent = round(done * 100 / total)
        report(phase=step["phase"], label=step["label"], percent=percent)
        try:
            kind = step["kind"]
            if kind == "run":
                detail = (lambda line: report(phase=step["phase"], label=step["label"], percent=percent,
                                              detail=line[:120])) if step.get("stream") else None
                host.run(step["argv"], stdin=step.get("secret"), timeout=step.get("timeout", 900), on_line=detail)
            elif kind == "write":
                host.write(step["path"], step["text"], step["mode"])
            elif kind == "link":
                host.link(step["path"], step["target"])
            elif kind == "mkdir":
                host.mkdir(step["path"])
            elif kind == "wait":
                host.wait_for(step["paths"])
            elif kind == "pacman-conf":
                host.pacman_conf()
            elif kind == "fstab":
                host.write("/etc/fstab", host.capture(["genfstab", "-U", str(TARGET)]) + "\n", 0o644)
            elif kind == "copy-connections":
                host.copy_connections()
            else:
                raise CommandError("Unknown installer step")
        except (CommandError, OSError, subprocess.SubprocessError) as error:
            if step.get("optional"):
                continue
            try:
                host.run(["umount", "-R", str(TARGET)], timeout=60)
            except (CommandError, OSError):
                pass
            raise CommandError(f"{step['label']} failed: {str(error)[-400:]}") from error
        done += step["weight"]
    report(phase="done", label="PrismOS is installed", percent=100, done=True)


def run_install(raw, host=None, available=None):
    """Root half: called by prism-installer-helper with the JSON request from stdin."""
    if not live():
        raise CommandError("The installer only runs from the PrismOS live USB")
    try:
        plan = validate(json.loads(raw), available)
    except (ValueError, TypeError) as error:
        raise CommandError(str(error)) from error
    execute(steps(plan, firmware(), microcode()), host or Host())
    return 0


# ----------------------------------------------------------------------------
# Unprivileged half
# ----------------------------------------------------------------------------

def install(raw):
    """Validate, then hand the request to the polkit-protected helper and relay its progress."""
    if not live():
        raise CommandError("Installing is only available from the PrismOS live USB")
    try:
        request = json.loads(raw)
        validate(request)
    except (ValueError, TypeError) as error:
        raise CommandError(str(error)) from error
    if not shutil.which("pkexec"):
        raise CommandError("polkit is not installed")
    if not Path(HELPER).is_file():
        raise CommandError("The PrismOS installer helper is missing; reinstall prism-shell")
    emit(phase="authorization", label="Waiting for administrator approval", percent=0)
    process = subprocess.Popen(["pkexec", HELPER, "install"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, bufsize=1)
    process.stdin.write(json.dumps(request))
    process.stdin.close()
    finished = False
    for line in process.stdout:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("phase") and event.get("label"):
            finished = finished or event.get("done") is True
            emit(**{key: event[key] for key in ("phase", "label", "percent", "detail", "done") if key in event})
    error = process.stderr.read()[-700:]
    if process.wait() != 0 or not finished:
        raise CommandError(error.strip() or "Administrator approval was cancelled")
    return 0
