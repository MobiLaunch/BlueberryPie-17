"""Boot the real PrismOS shell QML under plain Qt Quick with stub Quickshell modules.

Needs PySide6 (Qt 6.8+). Runs the genuine `prismctl` bridge against an isolated
config directory, so settings, themes and favorites are real while hardware tools
simply report themselves unavailable.
"""
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
STUBS = ROOT/"tests/qmlstubs"

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Material")

from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, Qt, QTimer, QUrl, qInstallMessageHandler  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtQml import QQmlComponent, QQmlEngine  # noqa: E402
from PySide6.QtQuick import QQuickView  # noqa: E402

sys.path.insert(0, str(ROOT/"tests"))
from qml_runtime import stubs, wayland_stub  # noqa: E402,F401

FATAL = re.compile(r"ReferenceError|TypeError|Cannot assign|Binding loop|is not a type|is not installed|"
                   r"Unable to assign|Cannot read property|Cannot call method|is not defined|"
                   r"not a function|Invalid property|Non-existent attached|Required property|"
                   r"module .* is not installed|File not found|Cyclic|Type .* unavailable")


class Harness:
    def __init__(self, width=1280, height=800, shell_dir=None, files_home=None):
        self.messages = []
        qInstallMessageHandler(self._capture)
        self.app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])
        self.shell_dir = Path(shell_dir or ROOT/"shell").resolve()
        self.sandbox = Path(tempfile.mkdtemp(prefix="prism-harness-"))
        self._prepare_environment(files_home)
        self.screen = stubs.ShellScreen("HARNESS-1", width, height)
        self.info = stubs.HarnessInfo(str(self.shell_dir), [self.screen])
        self.services = stubs.register(self.info)
        self.engine = QQmlEngine()
        self.engine.addImportPath(str(STUBS))
        self.engine.addImportPath(str(self.shell_dir))
        self.engine.rootContext().setContextProperty("Harness", self.info)
        self.view = QQuickView(self.engine, None)
        self.view.setResizeMode(QQuickView.SizeRootObjectToView)
        self.view.resize(width, height)
        self.view.setSource(QUrl.fromLocalFile(str(ROOT/"tests/qml_runtime/Desk.qml")))
        self.view.show()
        self.shell = None
        self._component = None

    # -- environment ------------------------------------------------------
    def _prepare_environment(self, files_home):
        box = self.sandbox
        self._saved_env = dict(os.environ)
        for name in ("config", "data/applications", "cache", "state", "runtime"):
            (box/name).mkdir(parents=True, exist_ok=True)
        (box/"runtime").chmod(0o700)
        home = Path(files_home) if files_home else box/"home"
        home.mkdir(parents=True, exist_ok=True)
        os.environ.update({
            "HOME": str(home), "XDG_CONFIG_HOME": str(box/"config"), "XDG_DATA_HOME": str(box/"data"),
            "XDG_DATA_DIRS": str(box/"empty-data"), "XDG_CACHE_HOME": str(box/"cache"),
            "XDG_STATE_HOME": str(box/"state"), "XDG_RUNTIME_DIR": str(box/"runtime"),
            "PATH": f"{ROOT/'bin'}:{os.environ.get('PATH', '')}",
        })

    def add_desktop_entry(self, filename, name, exec_="true", icon="application-x-executable", extra=""):
        path = self.sandbox/"data/applications"/filename
        path.write_text(f"[Desktop Entry]\nType=Application\nName={name}\nExec={exec_}\nIcon={icon}\n{extra}")
        return path

    def write_settings(self, **values):
        import json
        folder = self.sandbox/"config/prismos"
        folder.mkdir(parents=True, exist_ok=True)
        (folder/"settings.json").write_text(json.dumps(values))

    # -- diagnostics ------------------------------------------------------
    def _capture(self, mode, context, message):
        self.messages.append(message)

    def problems(self):
        return [line for line in self.messages if FATAL.search(line)]

    def warnings(self):
        return [line for line in self.messages if "Warning" in line or FATAL.search(line) or "qrc:" in line or ".qml" in line]

    # -- lifecycle --------------------------------------------------------
    def load(self, entry="shell.qml"):
        self._component = QQmlComponent(self.engine, QUrl.fromLocalFile(str(self.shell_dir/entry)))
        component = self._component
        self.shell = component.create()
        if self.shell is None:
            raise RuntimeError("Shell failed to load:\n" + "\n".join(e.toString() for e in component.errors()))
        return self.shell

    def pump(self, milliseconds=300):
        end = time.monotonic() + milliseconds/1000
        while time.monotonic() < end:
            self.app.processEvents()
            QCoreApplication.sendPostedEvents(None, 0)
            time.sleep(0.005)

    def wait_for(self, predicate, timeout=6000, step=50):
        end = time.monotonic() + timeout/1000
        while time.monotonic() < end:
            self.pump(step)
            if predicate():
                return True
        return False

    def ipc(self, function):
        handlers = [child for child in self.shell.findChildren(QObject) if child.metaObject().className().startswith("IpcHandler")]
        for handler in handlers:
            if QMetaObject.invokeMethod(handler, function):
                return True
        raise RuntimeError(f"No IPC function {function}")

    def screenshot(self, path):
        self.pump(120)
        image = self.view.grabWindow()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        image.save(str(path))
        return path

    def find(self, name):
        """First QML object whose objectName matches."""
        return self.shell.findChild(QObject, name, Qt.FindChildrenRecursively) or \
            self.view.rootObject().findChild(QObject, name, Qt.FindChildrenRecursively)

    def close(self):
        self.view.close()
        if self.shell is not None:
            self.shell.deleteLater()
            self.shell = None
        self._component = None
        self.view.setSource(QUrl())
        self.view.deleteLater()
        self.engine.deleteLater()
        for _ in range(4):  # deferred deletes need a few event-loop turns
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            self.app.processEvents()
        os.environ.clear()
        os.environ.update(self._saved_env)
        shutil.rmtree(self.sandbox, ignore_errors=True)
