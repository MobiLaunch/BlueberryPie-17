import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prismos import cli, inputs, installer, regional, settings
from prismos.system import CommandError

ROOT = Path(__file__).resolve().parent.parent
GB = 1000 ** 3


def part(path, size=1 * GB, fstype="", label="", mounts=None):
    return {"name": path, "path": path, "size": size, "type": "part", "fstype": fstype or None,
            "label": label or None, "mountpoints": mounts or [None]}


def disk(path, size=500 * GB, children=(), **extra):
    node = {"name": path, "path": path, "size": size, "type": "disk", "model": "Test Disk", "tran": "nvme",
            "ro": False, "rm": False, "mountpoints": [None], "children": list(children)}
    node.update(extra)
    return node


TREE = {"blockdevices": [
    disk("/dev/nvme0n1", children=[part("/dev/nvme0n1p1", fstype="ntfs", label="Windows")]),
    disk("/dev/sda", size=32 * GB, rm=True, tran="usb", children=[
        part("/dev/sda1", fstype="iso9660", label="PRISM_202610", mounts=["/run/archiso/bootmnt"]),
        part("/dev/sda2", fstype="vfat", label="ARCHISO_EFI")]),
    disk("/dev/sdb", size=64 * GB, children=[part("/dev/sdb1", fstype="ext4", mounts=["/mnt/data"])]),
    disk("/dev/sdc", size=8 * GB),
    disk("/dev/sdd", size=64 * GB, ro=True),
    disk("/dev/vda", size=40 * GB),
    {"name": "/dev/zram0", "path": "/dev/zram0", "size": 4 * GB, "type": "disk", "mountpoints": ["[SWAP]"]},
    {"name": "/dev/loop0", "path": "/dev/loop0", "size": 1 * GB, "type": "loop", "mountpoints": ["/x"]},
]}


def request(**changes):
    value = {"disk": "/dev/vda", "confirm": "vda", "hostname": "prism-box", "username": "alex",
             "fullname": "Alex Doe", "password": "correct horse", "timezone": "UTC",
             "locale": "en_US.UTF-8", "keyboard": "us"}
    value.update(changes)
    return value


class Recorder:
    def __init__(self, fail_on=None, fail_word=None):
        self.calls, self.stdin, self.writes, self.fail_on, self.fail_word = [], {}, {}, fail_on, fail_word

    def run(self, argv, stdin=None, timeout=900, on_line=None):
        self.calls.append(argv)
        if stdin is not None:
            self.stdin[argv[-1]] = stdin
        if on_line:
            on_line("installing something")
        if (self.fail_on and argv[0] == self.fail_on) or (self.fail_word and self.fail_word in argv):
            raise CommandError("boom")

    def capture(self, argv):
        self.calls.append(argv)
        return "# fstab"

    def write(self, path, text, mode):
        self.writes[path] = (text, mode)

    def link(self, path, target):
        self.writes[path] = ("->" + target, 0)

    def mkdir(self, path):
        self.calls.append(["mkdir", path])

    def wait_for(self, paths, seconds=30):
        self.calls.append(["wait", *paths])

    def pacman_conf(self):
        self.calls.append(["pacman-conf"])

    def copy_connections(self):
        self.calls.append(["copy-connections"])


class DiskTests(unittest.TestCase):
    def listed(self):
        return {item["path"]: item for item in installer.disks(TREE)}

    def test_only_real_whole_disks_are_listed(self):
        self.assertEqual(sorted(self.listed()), ["/dev/nvme0n1", "/dev/sda", "/dev/sdb", "/dev/sdc", "/dev/sdd", "/dev/vda"])

    def test_live_usb_is_never_eligible(self):
        usb = self.listed()["/dev/sda"]
        self.assertFalse(usb["eligible"])
        self.assertIn("started from", usb["reason"])

    def test_live_usb_is_recognised_by_label_after_copy_to_ram(self):
        tree = {"blockdevices": [disk("/dev/sde", size=64 * GB, children=[part("/dev/sde1", fstype="iso9660", label="PRISM_202610")])]}
        self.assertFalse(installer.disks(tree)[0]["eligible"])

    def test_mounted_small_and_readonly_disks_are_not_eligible(self):
        listed = self.listed()
        self.assertIn("In use", listed["/dev/sdb"]["reason"])
        self.assertIn("Smaller", listed["/dev/sdc"]["reason"])
        self.assertEqual(listed["/dev/sdd"]["reason"], "Read-only")

    def test_ordinary_disks_are_eligible_and_sorted_first(self):
        result = installer.disks(TREE)
        self.assertEqual([item["path"] for item in result[:2]], ["/dev/nvme0n1", "/dev/vda"])
        self.assertTrue(all(item["eligible"] for item in result[:2]))
        self.assertEqual(result[0]["partitions"][0]["fstype"], "ntfs")

    def test_a_stale_installer_mount_does_not_block_a_retry(self):
        tree = {"blockdevices": [disk("/dev/vda", size=40 * GB, children=[part("/dev/vda2", mounts=[str(installer.TARGET)])])]}
        self.assertTrue(installer.disks(tree)[0]["eligible"])

    def test_lsblk_failure_is_reported(self):
        with patch("prismos.installer.run", return_value="not json"):
            with self.assertRaises(CommandError):
                installer.disks()

    def test_partition_names_follow_kernel_convention(self):
        self.assertEqual(installer.partition_path("/dev/sda", 2), "/dev/sda2")
        self.assertEqual(installer.partition_path("/dev/nvme0n1", 2), "/dev/nvme0n1p2")
        self.assertEqual(installer.partition_path("/dev/mmcblk0", 1), "/dev/mmcblk0p1")


class ValidationTests(unittest.TestCase):
    def check(self, **changes):
        return installer.validate(request(**changes), available=installer.disks(TREE))

    def test_valid_request_is_normalized(self):
        plan = self.check(hostname="  Prism-Box ")
        self.assertEqual(plan["hostname"], "prism-box")
        self.assertEqual(plan["keyboard"]["console"], "us")

    def test_typed_confirmation_is_required(self):
        for wrong in ("", None, "sda", "/dev/vda", "VDA"):
            with self.assertRaises(ValueError, msg=wrong):
                self.check(confirm=wrong)

    def test_ineligible_and_unknown_disks_are_refused(self):
        for path, name in (("/dev/sda", "sda"), ("/dev/sdb", "sdb"), ("/dev/sdz", "sdz"), ("/dev/loop0", "loop0")):
            with self.assertRaises(ValueError, msg=path):
                self.check(disk=path, confirm=name)

    def test_disk_path_cannot_carry_extra_text(self):
        for path in ("/dev/vda; rm -rf /", "/dev/vda ", "vda", "/dev/../etc/passwd", "/dev/vda\n", ["/dev/vda"], None):
            with self.assertRaises(ValueError, msg=repr(path)):
                self.check(disk=path)

    def test_names_and_passwords_are_constrained(self):
        bad = {"hostname": ["-bad", "has space", "UP_per", "a" * 64, ""],
               "username": ["root", "Alex", "1abc", "a b", "greeter", "systemd-x", "", "x" * 33],
               "fullname": ["a:b", "a,b", "a\nb", "x" * 65],
               "password": ["short", "x" * 129, "line\nbreak", None, 12345678],
               "timezone": ["Mars/Base", "../etc/passwd", "", None],
               "locale": ["xx_XX.UTF-8", "en_US.UTF-8; rm", None],
               "keyboard": ["qwertz", "../x", None]}
        for field, values in bad.items():
            for value in values:
                with self.assertRaises(ValueError, msg=f"{field}={value!r}"):
                    self.check(**{field: value})

    def test_non_object_request_is_refused(self):
        for value in (None, [], "x", 3):
            with self.assertRaises(ValueError):
                installer.validate(value, available=[])


class StepTests(unittest.TestCase):
    def plan(self, **changes):
        return installer.validate(request(**changes), available=installer.disks(TREE))

    def build(self, mode="uefi", **changes):
        return installer.steps(self.plan(**changes), mode, "intel-ucode")

    def argvs(self, built):
        return [step["argv"] for step in built if "argv" in step]

    def index(self, built, first):
        return next(i for i, step in enumerate(built) if step.get("argv", [None])[0:1] == [first]
                    or (len(step.get("argv", [])) > 2 and step["argv"][2:3] == [first]))

    def test_every_command_is_a_plain_argv_list(self):
        for mode in ("uefi", "bios"):
            for argv in self.argvs(self.build(mode)):
                self.assertIsInstance(argv, list)
                self.assertTrue(all(isinstance(item, str) for item in argv))
                self.assertNotIn(argv[0], ("sh", "bash", "dash", "zsh", "eval"))
                self.assertFalse(any(item in ("-c", "--rcfile") for item in argv[1:2]), argv)

    def test_destructive_commands_only_touch_the_chosen_disk(self):
        built = self.build()
        allowed = {"/dev/vda", "/dev/vda1", "/dev/vda2"}
        devices = {item for argv in self.argvs(built) for item in argv if item.startswith("/dev/")}
        self.assertEqual(devices, allowed)

    def test_password_is_only_ever_sent_on_stdin_to_chpasswd(self):
        built = self.build(password="s3cret pass")
        for step in built:
            for value in step.get("argv", []):
                self.assertNotIn("s3cret", value)
        secrets = [step for step in built if step.get("secret")]
        self.assertEqual(len(secrets), 1)
        self.assertEqual(secrets[0]["argv"][-1], "chpasswd")
        self.assertEqual(secrets[0]["secret"], "alex:s3cret pass\n")

    def test_uefi_order_and_layout(self):
        built = self.build("uefi")
        names = [argv[0] if argv[0] != "arch-chroot" else argv[2] for argv in self.argvs(built)]
        for earlier, later in (("wipefs", "sgdisk"), ("sgdisk", "mkfs.ext4"), ("mkfs.fat", "mount"), ("mount", "pacstrap"),
                               ("pacstrap", "useradd"), ("useradd", "chpasswd"), ("chpasswd", "systemctl"),
                               ("systemctl", "grub-install"), ("grub-install", "grub-mkconfig"), ("grub-mkconfig", "sync")):
            self.assertLess(names.index(earlier), names.index(later), (earlier, later))
        table = next(argv for argv in self.argvs(built) if argv[0] == "sgdisk" and "--zap-all" not in argv)
        self.assertIn("--typecode=1:ef00", table)
        self.assertIn("--new=1:0:+1024M", table)
        self.assertEqual(names[-1], "umount")
        pacstrap = next(argv for argv in self.argvs(built) if argv[0] == "pacstrap")
        for package in ("base", "linux", "prism-shell", "greetd", "intel-ucode", "efibootmgr", "grub"):
            self.assertIn(package, pacstrap)
        self.assertEqual(sum(1 for argv in self.argvs(built) if "grub-install" in argv), 2)
        self.assertTrue(any("--removable" in argv for argv in self.argvs(built)))

    def test_bios_layout_uses_a_bios_boot_partition_and_no_esp(self):
        built = self.build("bios")
        argvs = self.argvs(built)
        table = next(argv for argv in argvs if argv[0] == "sgdisk" and "--zap-all" not in argv)
        self.assertIn("--typecode=1:ef02", table)
        self.assertFalse(any(argv[0] == "mkfs.fat" for argv in argvs))
        self.assertIn(["arch-chroot", str(installer.TARGET), "grub-install", "--target=i386-pc", "/dev/vda"], argvs)
        self.assertNotIn("efibootmgr", next(argv for argv in argvs if argv[0] == "pacstrap"))

    def test_nvme_partitions_are_derived_correctly(self):
        plan = installer.validate(request(disk="/dev/nvme0n1", confirm="nvme0n1"), available=installer.disks(TREE))
        argvs = self.argvs(installer.steps(plan, "uefi", None))
        self.assertIn(["mkfs.ext4", "-F", "-L", "prismos", "/dev/nvme0n1p2"], argvs)
        self.assertIn(["mount", "/dev/nvme0n1p2", str(installer.TARGET)], argvs)
        self.assertNotIn("intel-ucode", next(argv for argv in argvs if argv[0] == "pacstrap"))

    def test_account_files_and_system_settings(self):
        plan = self.plan(timezone="Europe/Lisbon" if "Europe/Lisbon" in regional.timezones() else "UTC",
                         locale="pt_PT.UTF-8", keyboard="pt", fullname="")
        built = installer.steps(plan, "uefi", None)
        writes = {step["path"]: step for step in built if step["kind"] == "write"}
        self.assertEqual(writes["/etc/hostname"]["text"], "prism-box\n")
        self.assertEqual(writes["/etc/locale.conf"]["text"], "LANG=pt_PT.UTF-8\n")
        self.assertEqual(writes["/etc/locale.gen"]["text"], "pt_PT.UTF-8 UTF-8\nen_US.UTF-8 UTF-8\n")
        self.assertEqual(writes["/etc/vconsole.conf"]["text"], "KEYMAP=pt-latin1\n")
        self.assertEqual(writes["/etc/sudoers.d/10-wheel"]["mode"], 0o440)
        self.assertEqual(json.loads(writes["/home/alex/.config/prismos/settings.json"]["text"]), {"keyboard": "pt"})
        self.assertNotIn("--comment", next(argv for argv in self.argvs(built) if "useradd" in argv))
        self.assertIn("--remember", writes["/etc/greetd/config.toml"]["text"])
        self.assertNotIn("initial_session", writes["/etc/greetd/config.toml"]["text"])
        self.assertTrue(any(step["kind"] == "link" and step["path"] == "/etc/localtime" for step in built))
        self.assertTrue(any(argv[2:4] == ["passwd", "--lock"] for argv in self.argvs(built) if argv[0] == "arch-chroot"))

    def test_full_name_reaches_useradd_as_one_argument(self):
        useradd = next(argv for argv in self.argvs(self.build(fullname="Alex Doe")) if "useradd" in argv)
        self.assertEqual(useradd[useradd.index("--comment") + 1], "Alex Doe")
        self.assertEqual(useradd[-1], "alex")

    def test_preview_never_contains_the_password(self):
        with patch("prismos.installer.firmware", return_value="uefi"), patch("prismos.installer.microcode", return_value=None):
            shown = installer.preview(request(password="hunter2hunter2"), available=installer.disks(TREE))
        self.assertNotIn("hunter2", json.dumps(shown))
        self.assertEqual(shown["partitions"][0]["name"], "EFI system partition")
        self.assertTrue(any("password supplied privately" in step["command"] for step in shown["steps"]))
        self.assertEqual(shown["disk_name"], "vda")


class ExecuteTests(unittest.TestCase):
    def run_plan(self, host, mode="uefi"):
        plan = installer.validate(request(), available=installer.disks(TREE))
        events = []
        installer.execute(installer.steps(plan, mode, None), host, lambda **event: events.append(event))
        return events

    def test_progress_is_monotonic_and_ends_done(self):
        events = self.run_plan(Recorder())
        percents = [event["percent"] for event in events]
        self.assertEqual(percents, sorted(percents))
        self.assertEqual(events[-1], {"phase": "done", "label": "PrismOS is installed", "percent": 100, "done": True})
        self.assertIn("packages", {event["phase"] for event in events})
        self.assertTrue(any(event.get("detail") == "installing something" for event in events))

    def test_password_is_delivered_on_stdin_and_never_reported(self):
        host = Recorder()
        events = self.run_plan(host)
        self.assertEqual(host.stdin["chpasswd"], "alex:correct horse\n")
        self.assertNotIn("correct horse", json.dumps(events))

    def test_a_failure_stops_the_install_and_unmounts(self):
        host = Recorder(fail_on="pacstrap")
        with self.assertRaises(CommandError) as context:
            self.run_plan(host)
        self.assertIn("failed", str(context.exception))
        self.assertEqual(host.calls[-1], ["umount", "-R", str(installer.TARGET)])
        self.assertFalse(any(argv[0] == "arch-chroot" for argv in host.calls))

    def test_optional_steps_may_fail(self):
        host = Recorder(fail_word="hwclock")
        events = self.run_plan(host)  # the clock sync is best-effort in virtual machines
        self.assertEqual(events[-1]["done"], True)
        self.assertIn(["arch-chroot", str(installer.TARGET), "hwclock", "--systohc"], host.calls)

    def test_required_steps_may_not_fail_silently(self):
        for word in ("sgdisk", "mkfs.ext4", "useradd", "chpasswd", "grub-mkconfig"):
            with self.assertRaises(CommandError, msg=word):
                self.run_plan(Recorder(fail_word=word))

    def test_helper_reports_secret_free_error(self):
        host = Recorder(fail_on="mkfs.ext4")
        with self.assertRaises(CommandError) as context:
            self.run_plan(host)
        self.assertNotIn("correct horse", str(context.exception))


class RootHalfTests(unittest.TestCase):
    def test_refuses_outside_the_live_usb(self):
        with patch("prismos.installer.live", return_value=False):
            with self.assertRaisesRegex(CommandError, "live USB"):
                installer.run_install(json.dumps(request()), Recorder(), installer.disks(TREE))

    def test_revalidates_the_request(self):
        with patch("prismos.installer.live", return_value=True):
            with self.assertRaises(CommandError):
                installer.run_install(json.dumps(request(confirm="nope")), Recorder(), installer.disks(TREE))
            with self.assertRaises(CommandError):
                installer.run_install("{not json", Recorder(), installer.disks(TREE))

    def test_runs_all_steps_on_the_live_usb(self):
        host = Recorder()
        with patch("prismos.installer.live", return_value=True), patch("prismos.installer.firmware", return_value="bios"), \
                patch("prismos.installer.microcode", return_value=None), redirect() as out:
            self.assertEqual(installer.run_install(json.dumps(request()), host, installer.disks(TREE)), 0)
        self.assertEqual(json.loads(out.getvalue().splitlines()[-1])["done"], True)
        self.assertIn(["pacstrap", "-K", "-C", str(installer.WORK / "pacman.conf"), str(installer.TARGET),
                       *installer.BASE_PACKAGES], host.calls)

    def test_helper_script_rejects_unprivileged_or_unknown_use(self):
        helper = ROOT / "bin" / "prism-installer-helper"
        for args in ([], ["install"], ["wipe"]):
            outcome = subprocess.run([sys.executable, "-I", str(helper), *args], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30)
            if os.geteuid() != 0 or args != ["install"]:
                self.assertEqual(outcome.returncode, 2, (args, outcome.stderr))
            self.assertNotIn("Traceback", outcome.stderr)


class HostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / "target" / "etc").mkdir(parents=True)
        self.root = root
        for name, value in (("TARGET", root / "target"), ("WORK", root)):
            patcher = patch.object(installer, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_writes_stay_inside_the_target_with_requested_mode(self):
        host = installer.Host()
        host.write("/etc/hostname", "box\n", 0o600)
        written = self.root / "target/etc/hostname"
        self.assertEqual(written.read_text(), "box\n")
        self.assertEqual(written.stat().st_mode & 0o777, 0o600)

    def test_escape_attempts_are_refused(self):
        host = installer.Host()
        with self.assertRaises(CommandError):
            host.write("/../outside", "x", 0o644)
        (self.root / "outside").mkdir()
        (self.root / "target/etc/evil").symlink_to(self.root / "outside")
        with self.assertRaises(CommandError):
            host.write("/etc/evil/file", "x", 0o644)
        (self.root / "target/etc/link").symlink_to(self.root / "outside" / "f")
        with self.assertRaises(OSError):
            host.write("/etc/link", "x", 0o644)  # O_NOFOLLOW

    def test_localtime_link_replaces_an_existing_file(self):
        host = installer.Host()
        (self.root / "target/etc/localtime").write_text("old")
        host.link("/etc/localtime", "/usr/share/zoneinfo/UTC")
        self.assertEqual(os.readlink(self.root / "target/etc/localtime"), "/usr/share/zoneinfo/UTC")

    def test_pacman_conf_gains_the_bundled_repo_once(self):
        conf = self.root / "pacman.src"
        conf.write_text("[options]\nHoldPkg = pacman\n\n[core]\nInclude = /etc/pacman.d/mirrorlist\n\n[prismos]\nServer = file:///stale\n")
        repo = self.root / "repo"
        repo.mkdir()
        with patch.object(installer, "PACMAN_CONF", conf), patch.object(installer, "OFFLINE_REPO", repo):
            installer.Host().pacman_conf()
        text = (self.root / "pacman.conf").read_text()
        self.assertEqual(text.count("[prismos]"), 1)
        self.assertNotIn("stale", text)
        self.assertIn(f"Server = file://{repo}", text)
        self.assertIn("[core]", text)

    def test_saved_wifi_profiles_are_copied_private(self):
        source = self.root / "nm"
        source.mkdir()
        (source / "Home.nmconnection").write_text("[wifi]\n")
        (source / "notes.txt").write_text("skip")
        with patch.object(installer, "NM_CONNECTIONS", source):
            installer.Host().copy_connections()
        copied = self.root / "target/etc/NetworkManager/system-connections"
        self.assertEqual([item.name for item in copied.iterdir()], ["Home.nmconnection"])
        self.assertEqual((copied / "Home.nmconnection").stat().st_mode & 0o777, 0o600)

    def test_streamed_commands_report_lines_and_failures(self):
        lines = []
        installer.Host().run(["printf", "one\\ntwo\\n"], on_line=lines.append)
        self.assertEqual(lines, ["one", "two"])
        with self.assertRaisesRegex(CommandError, "nope"):
            installer.Host().run(["sh", "-c", "echo nope; exit 3"])
        self.assertEqual(installer.Host().run(["cat"], stdin="in\n"), "in")


@contextlib.contextmanager
def redirect():
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        yield buffer


class CliTests(unittest.TestCase):
    def call(self, argv, stdin=""):
        with patch("sys.stdin", io.StringIO(stdin)), redirect() as out:
            code = cli.main(argv)
        return code, out.getvalue()

    @patch("prismos.installer.run")
    def test_disks_and_status_are_json(self, run):
        run.side_effect = lambda argv, timeout=4: json.dumps(TREE) if argv[0] == "lsblk" else "full"
        code, text = self.call(["installer", "disks"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(text)["disks"][0]["path"], "/dev/nvme0n1")
        code, text = self.call(["installer", "status"])
        state = json.loads(text)
        self.assertEqual((code, state["ok"], state["online"]), (0, True, True))
        self.assertIn(state["firmware"], ("uefi", "bios"))

    def test_options_list_locales_keyboards_and_zones(self):
        code, text = self.call(["installer", "options"])
        data = json.loads(text)
        self.assertEqual(code, 0)
        self.assertEqual(data["keyboards"][0], {"id": "us", "label": "English (US)"})
        self.assertIn("UTC", data["timezones"])

    @patch("prismos.installer.disks", return_value=installer.disks(TREE))
    def test_plan_previews_and_rejects_bad_input(self, disks):
        code, text = self.call(["installer", "plan"], json.dumps(request()))
        self.assertEqual((code, json.loads(text)["disk_name"]), (0, "vda"))
        code, text = self.call(["installer", "plan"], json.dumps(request(confirm="x")))
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(text)["ok"])
        code, text = self.call(["installer", "plan"], "not json")
        self.assertEqual(code, 1)

    @patch("prismos.installer.live", return_value=False)
    def test_install_refuses_off_the_live_usb(self, live):
        code, text = self.call(["installer", "install"], json.dumps(request()))
        self.assertEqual(code, 1)
        self.assertIn("live USB", json.loads(text)["error"])

    @patch("prismos.installer.shutil.which", return_value="/usr/bin/pkexec")
    @patch("prismos.installer.Path.is_file", return_value=True)
    @patch("prismos.installer.subprocess.Popen")
    @patch("prismos.installer.disks", return_value=installer.disks(TREE))
    @patch("prismos.installer.live", return_value=True)
    def test_install_relays_helper_progress_and_never_echoes_input(self, live, disks, popen, is_file, which):
        process = popen.return_value
        process.stdin = io.StringIO()
        process.stdin.close = lambda: None
        process.stdout = iter([json.dumps({"ok": True, "phase": "format", "label": "Formatting", "percent": 4}) + "\n", "noise\n",
                               json.dumps({"ok": True, "phase": "done", "label": "PrismOS is installed", "percent": 100, "done": True}) + "\n"])
        process.stderr = io.StringIO("")
        process.wait.return_value = 0
        code, text = self.call(["installer", "install"], json.dumps(request()))
        events = [json.loads(line) for line in text.splitlines()]
        self.assertEqual(code, 0)
        self.assertEqual([event["phase"] for event in events], ["authorization", "format", "done"])
        self.assertNotIn("correct horse", text)
        self.assertEqual(popen.call_args.args[0], ["pkexec", installer.HELPER, "install"])
        self.assertIn("correct horse", process.stdin.getvalue())

    @patch("prismos.installer.shutil.which", return_value="/usr/bin/pkexec")
    @patch("prismos.installer.Path.is_file", return_value=True)
    @patch("prismos.installer.subprocess.Popen")
    @patch("prismos.installer.disks", return_value=installer.disks(TREE))
    @patch("prismos.installer.live", return_value=True)
    def test_cancelled_authorization_is_an_error(self, live, disks, popen, is_file, which):
        process = popen.return_value
        process.stdin = io.StringIO()
        process.stdin.close = lambda: None
        process.stdout = iter([])
        process.stderr = io.StringIO("Error executing command as another user: Not authorized")
        process.wait.return_value = 126
        code, text = self.call(["installer", "install"], json.dumps(request()))
        self.assertEqual(code, 1)
        self.assertIn("Not authorized", json.loads(text.splitlines()[-1])["error"])


class KeyboardSettingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patcher = patch.dict(os.environ, {"XDG_CONFIG_HOME": self.temp.name})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_unknown_layouts_are_ignored(self):
        settings.directory().mkdir()
        (settings.directory() / "settings.json").write_text('{"keyboard": "../etc"}')
        self.assertEqual(settings.load()["keyboard"], "us")
        settings.update(keyboard="de")
        self.assertEqual(settings.load()["keyboard"], "de")

    @patch("prismos.inputs.run")
    def test_session_applies_the_saved_layout(self, run):
        settings.update(keyboard="dvorak")
        inputs.apply()
        calls = [entry.args[0] for entry in run.call_args_list]
        self.assertIn(["hyprctl", "keyword", "input:kb_layout", "us"], calls)
        self.assertIn(["hyprctl", "keyword", "input:kb_variant", "dvorak"], calls)


class PackagingTests(unittest.TestCase):
    def test_policy_helper_and_package_agree(self):
        policy = (ROOT / "packaging/polkit/org.prismos.installer.policy").read_text()
        self.assertIn(f'>{installer.HELPER}<', policy)
        self.assertIn("auth_admin", policy)
        pkgbuild = (ROOT / "packaging/arch/PKGBUILD").read_text()
        self.assertIn(f'"${{pkgdir}}{installer.HELPER}"', pkgbuild)
        self.assertIn("org.prismos.installer.policy", pkgbuild)
        self.assertTrue(os.access(ROOT / "bin/prism-installer-helper", os.X_OK))

    def test_live_image_carries_installer_tools_and_bundled_repo(self):
        packages = (ROOT / "archiso/packages.x86_64").read_text().split()
        for needed in ("arch-install-scripts", "gptfdisk", "dosfstools", "e2fsprogs", "grub", "efibootmgr", "polkit"):
            self.assertIn(needed, packages)
        build = (ROOT / "scripts/build-iso.sh").read_text()
        self.assertIn("opt/prismos/repo", build)
        self.assertIn("prismos-installer.desktop", build)
        self.assertIn("installer", (ROOT / "bin/prism-shell").read_text())

    def test_installed_packages_are_real_and_include_the_desktop(self):
        self.assertIn("prism-shell", installer.BASE_PACKAGES)
        self.assertEqual(len(installer.BASE_PACKAGES), len(set(installer.BASE_PACKAGES)))
        live = (ROOT / "archiso/packages.x86_64").read_text().split()
        for name in ("greetd", "greetd-tuigreet", "firefox", "mesa", "vulkan-intel", "vulkan-radeon", "zram-generator"):
            if name in installer.BASE_PACKAGES and name != "zram-generator":
                self.assertIn(name, live, name)

    def test_shell_services_exist_in_the_package_list(self):
        self.assertEqual(set(installer.SERVICES), {"NetworkManager.service", "bluetooth.service", "greetd.service",
                                                   "systemd-timesyncd.service"})
        self.assertIn("bluez", (ROOT / "packaging/arch/PKGBUILD").read_text())


if __name__ == "__main__":
    unittest.main()
