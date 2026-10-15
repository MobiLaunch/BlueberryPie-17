"""Stand-ins for the Quickshell modules PrismOS imports.

These let the real shell QML load under plain Qt Quick (PySide6) so binding,
reference and type errors surface without a compositor. They are an
approximation: layer-shell focus, input regions, D-Bus services and Hyprland
IPC are not modelled. A passing run is *not* Quickshell/Hyprland qualification.
"""
import os

from PySide6.QtCore import (Property, QAbstractListModel, QByteArray, QModelIndex, QObject,
                            QProcess, QProcessEnvironment, Qt, Signal, Slot)
from PySide6.QtQml import qmlRegisterSingletonType, qmlRegisterType


def prop(kind, name, default=None, notify_name=None):
    """A read/write notifying property backed by `_name`."""
    signal = Signal()

    def getter(self):
        return self.__dict__.get("_" + name, default)

    def setter(self, value):
        if self.__dict__.get("_" + name, default) != value:
            self.__dict__["_" + name] = value
            getattr(self, (notify_name or name + "Changed")).emit()

    return signal, Property(kind, getter, setter, notify=signal)


class ObjectList(QAbstractListModel):
    """Quickshell's UntypedObjectModel: usable as a model and via `.values`."""
    valuesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._items)

    def data(self, index, role=Qt.UserRole):
        if not index.isValid() or index.row() >= len(self._items):
            return None
        return self._items[index.row()]

    def roleNames(self):
        return {Qt.UserRole: QByteArray(b"modelData")}

    @Property("QVariantList", notify=valuesChanged)
    def values(self):
        return list(self._items)

    def add(self, item):
        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append(item)
        self.endInsertRows()
        self.valuesChanged.emit()

    def remove(self, item):
        if item in self._items:
            row = self._items.index(item)
            self.beginRemoveRows(QModelIndex(), row, row)
            self._items.pop(row)
            self.endRemoveRows()
            self.valuesChanged.emit()


# --- Quickshell.Io ----------------------------------------------------------
class StdioCollector(QObject):
    textChanged = Signal()
    streamFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buffer = b""

    @Property(str, notify=textChanged)
    def text(self):
        return self._buffer.decode("utf-8", "replace")

    def feed(self, data):
        self._buffer += bytes(data)
        self.textChanged.emit()

    def finish(self):
        try:
            self.streamFinished.emit()
        except RuntimeError:  # collector already destroyed with its Process
            pass

    def reset(self):
        self._buffer = b""
        self.textChanged.emit()


class SplitParser(QObject):
    read = Signal(str)
    splitMarkerChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pending = b""
        self._marker = "\n"

    @Property(str, notify=splitMarkerChanged)
    def splitMarker(self):
        return self._marker

    @splitMarker.setter
    def splitMarker(self, value):
        self._marker = value
        self.splitMarkerChanged.emit()

    def feed(self, data):
        self._pending += bytes(data)
        marker = self._marker.encode()
        while marker in self._pending:
            line, self._pending = self._pending.split(marker, 1)
            self.read.emit(line.decode("utf-8", "replace"))

    def finish(self):
        if self._pending:
            self.read.emit(self._pending.decode("utf-8", "replace"))
            self._pending = b""

    def reset(self):
        self._pending = b""


class Process(QObject):
    """Runs the real command (argv only) so the real prismctl bridge answers."""
    commandChanged = Signal()
    runningChanged = Signal()
    stdinEnabledChanged = Signal()
    stdoutChanged = Signal()
    started = Signal()
    exited = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._command, self._stdout, self._stdin, self._proc = [], None, False, None
        self.history = []

    def _set_command(self, value):
        self._command = [str(item) for item in (value.toVariant() if hasattr(value, "toVariant") else value)]
        self.commandChanged.emit()

    command = Property("QVariantList", lambda s: s._command, _set_command, notify=commandChanged)

    def _set_stdout(self, value):
        self._stdout = value
        self.stdoutChanged.emit()

    stdout = Property(QObject, lambda s: s._stdout, _set_stdout, notify=stdoutChanged)

    def _set_stdin(self, value):
        was = self._stdin
        self._stdin = bool(value)
        if was and not self._stdin and self._proc is not None:
            self._proc.closeWriteChannel()  # Quickshell closes the pipe when stdin is disabled
        self.stdinEnabledChanged.emit()

    stdinEnabled = Property(bool, lambda s: s._stdin, _set_stdin, notify=stdinEnabledChanged)

    def _set_running(self, value):
        if value and self._proc is None:
            self._start()
        elif not value and self._proc is not None:
            self._proc.terminate()

    running = Property(bool, lambda s: s._proc is not None, _set_running, notify=runningChanged)

    def _start(self):
        if not self._command:
            return
        proc = QProcess(self)
        proc.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
        if self._stdout is not None and hasattr(self._stdout, "reset"):
            self._stdout.reset()
        proc.readyReadStandardOutput.connect(lambda: self._pump(proc))
        proc.finished.connect(lambda code, status: self._done(proc, code, int(status.value) if hasattr(status, "value") else int(status)))
        proc.errorOccurred.connect(lambda error: self._failed(proc, error))
        self._proc = proc
        Process.log.append(list(self._command))
        self.runningChanged.emit()
        proc.start(self._command[0], self._command[1:])
        self.started.emit()

    log = []

    def _pump(self, proc):
        if self._proc is not proc:
            return
        try:
            data = proc.readAllStandardOutput()
        except RuntimeError:  # owner destroyed while the child was still running
            self._proc = None
            return
        if self._stdout is not None and hasattr(self._stdout, "feed"):
            self._stdout.feed(data)

    def _failed(self, proc, error):
        if error == QProcess.ProcessError.FailedToStart and self._proc is proc:
            self._done(proc, 127, 1)

    def _done(self, proc, code, status):
        if self._proc is not proc:
            return
        try:
            self._pump(proc)
            self._proc = None
            if self._stdout is not None and hasattr(self._stdout, "finish"):
                self._stdout.finish()
            self.runningChanged.emit()
            self.exited.emit(code, status)
            proc.deleteLater()
        except RuntimeError:  # the QML owner was destroyed while the command ran
            self._proc = None

    @Slot(str)
    def write(self, data):
        if self._proc is not None and self._stdin:
            self._proc.write(data.encode())

    @Slot()
    def closeStdin(self):
        if self._proc is not None:
            self._proc.closeWriteChannel()


class IpcHandler(QObject):
    targetChanged, target = prop(str, "target", "")


# --- Quickshell.Hyprland ----------------------------------------------------
class HyprlandMonitor(QObject):
    nameChanged, name = prop(str, "name", "")


class HyprlandEvent(QObject):
    def __init__(self, name, data, parent=None):
        super().__init__(parent)
        self.name_, self.data_ = name, data

    @Property(str, constant=True)
    def name(self):
        return self.name_

    @Property(str, constant=True)
    def data(self):
        return self.data_


class HyprlandToplevel(QObject):
    """Quickshell's HyprlandToplevel: a window address and its Wayland toplevel handle."""
    addressChanged, address = prop(str, "address", "")
    waylandChanged, wayland = prop(QObject, "wayland", None)


class HyprlandIpc(QObject):
    focusedMonitorChanged = Signal()
    rawEvent = Signal(QObject)
    toplevelsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._monitor = None
        self._toplevels = ObjectList(self)
        self.refreshes = 0

    @Property(QObject, notify=toplevelsChanged)
    def toplevels(self):
        return self._toplevels

    @Slot()
    def refreshToplevels(self):
        self.refreshes += 1

    def add_toplevel(self, address, with_handle=True):
        item = HyprlandToplevel(self)
        item.address = address
        item.wayland = QObject(self) if with_handle else None
        self._toplevels.add(item)

    @Property(QObject, notify=focusedMonitorChanged)
    def focusedMonitor(self):
        return self._monitor

    def focus(self, name):
        monitor = HyprlandMonitor(self)
        monitor.name = name
        self._monitor = monitor
        self.focusedMonitorChanged.emit()

    def emit_raw(self, name, data):
        self.rawEvent.emit(HyprlandEvent(name, data, self))


class HyprlandFocusGrab(QObject):
    activeChanged, active = prop(bool, "active", False)
    windowsChanged, windows = prop("QVariantList", "windows", [])
    cleared = Signal()


# --- Quickshell.Services.SystemTray ----------------------------------------
class SystemTrayService(QObject):
    itemsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = ObjectList(self)

    @Property(QObject, notify=itemsChanged)
    def items(self):
        return self._items


# --- Quickshell.Services.Notifications --------------------------------------
class NotificationAction(QObject):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self._text = text
        self.invoked = 0

    @Property(str, constant=True)
    def text(self):
        return self._text

    @Slot()
    def invoke(self):
        self.invoked += 1


class Notification(QObject):
    trackedChanged = Signal()
    closed = Signal()

    _next_id = [0]

    def __init__(self, server, appName="", summary="", body="", urgency=1, actions=(), desktopEntry="", appIcon="",
                 reply=None, parent=None):
        super().__init__(parent)
        Notification._next_id[0] += 1
        self._id = Notification._next_id[0]
        self._reply = reply  # None, or the placeholder text of an app that accepts inline replies
        self.server = server
        self._icon = appIcon
        self._app, self._summary, self._body = appName, summary, body
        self._urgency, self._desktop = urgency, desktopEntry
        self._actions = [NotificationAction(text, self) for text in actions]
        self._tracked = False

    appName = Property(str, lambda s: s._app, constant=True)
    summary = Property(str, lambda s: s._summary, constant=True)
    body = Property(str, lambda s: s._body, constant=True)
    urgency = Property(int, lambda s: s._urgency, constant=True)
    desktopEntry = Property(str, lambda s: s._desktop, constant=True)
    appIcon = Property(str, lambda s: s._icon, constant=True)
    actions = Property("QVariantList", lambda s: list(s._actions), constant=True)
    id = Property(int, lambda s: s._id, constant=True)
    hasInlineReply = Property(bool, lambda s: s._reply is not None, constant=True)
    inlineReplyPlaceholder = Property(str, lambda s: s._reply or "", constant=True)

    @Slot(str)
    def sendInlineReply(self, text):
        self.server.replies.append((self._id, text))

    def _set_tracked(self, value):
        if value and not self._tracked:
            self._tracked = True
            self.server.tracked.add(self)
        elif not value and self._tracked:
            self._tracked = False
            self.server.tracked.remove(self)
        self.trackedChanged.emit()

    tracked = Property(bool, lambda s: s._tracked, _set_tracked, notify=trackedChanged)

    @Slot()
    def dismiss(self):
        self._set_tracked(False)
        self.closed.emit()

    @Slot()
    def expire(self):
        self.dismiss()


class NotificationServer(QObject):
    trackedChanged = Signal()
    notification = Signal(QObject)
    bodySupportedChanged, bodySupported = prop(bool, "bodySupported", False)
    bodyMarkupSupportedChanged, bodyMarkupSupported = prop(bool, "bodyMarkupSupported", False)
    actionsSupportedChanged, actionsSupported = prop(bool, "actionsSupported", False)
    persistenceSupportedChanged, persistenceSupported = prop(bool, "persistenceSupported", False)
    inlineReplySupportedChanged, inlineReplySupported = prop(bool, "inlineReplySupported", False)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.replies = []
        self.tracked = ObjectList(self)
        NotificationServer.instances.append(self)

    instances = []

    @Property(QObject, notify=trackedChanged)
    def trackedNotifications(self):
        return self.tracked

    def post(self, **fields):
        note = Notification(self, **fields)
        self.notification.emit(note)
        return note


# --- Quickshell.Services.Mpris ---------------------------------------------
class MprisService(QObject):
    playersChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._players = ObjectList(self)

    @Property(QObject, notify=playersChanged)
    def players(self):
        return self._players


class MprisPlayer(QObject):
    changed = Signal()

    def __init__(self, dbusName, identity, title="", artist="", playing=False, parent=None):
        super().__init__(parent)
        self._fields = {"dbusName": dbusName, "identity": identity, "trackTitle": title,
                        "trackArtist": artist, "trackArtUrl": "", "isPlaying": playing,
                        "canTogglePlaying": True, "canGoNext": True, "canGoPrevious": True}

    def _field(name, kind, signal=changed):
        return Property(kind, lambda s: s._fields[name], notify=signal)

    dbusName = _field("dbusName", str)
    identity = _field("identity", str)
    trackTitle = _field("trackTitle", str)
    trackArtist = _field("trackArtist", str)
    trackArtUrl = _field("trackArtUrl", str)
    isPlaying = _field("isPlaying", bool)
    canTogglePlaying = _field("canTogglePlaying", bool)
    canGoNext = _field("canGoNext", bool)
    canGoPrevious = _field("canGoPrevious", bool)

    @Slot()
    def togglePlaying(self):
        self._fields["isPlaying"] = not self._fields["isPlaying"]
        self.changed.emit()

    @Slot()
    def next(self):
        pass

    @Slot()
    def previous(self):
        pass


class ShellScreen(QObject):
    def __init__(self, name, width, height, parent=None):
        super().__init__(parent)
        self._name, self._width, self._height = name, width, height

    name = Property(str, lambda s: s._name, constant=True)
    width = Property(int, lambda s: s._width, constant=True)
    height = Property(int, lambda s: s._height, constant=True)


ICON_ROOTS = ("/usr/share/icons/Adwaita", "/usr/share/icons/hicolor", "/usr/share/pixmaps")


def find_icon(name):
    """Best-effort icon-theme lookup; None when the theme lacks the icon."""
    import glob
    import re
    if not name or not re.fullmatch(r"[A-Za-z0-9._+-]{1,120}", name):
        return None
    if name.startswith("/") and os.path.isfile(name):
        return name
    for root in ICON_ROOTS:
        for pattern in (f"{root}/scalable/apps/{name}.svg", f"{root}/*/apps/{name}.svg",
                        f"{root}/*/apps/{name}.png", f"{root}/{name}.png", f"{root}/*/*/{name}.svg"):
            hits = sorted(glob.glob(pattern))
            if hits:
                return hits[-1]
    return None


def placeholder_icon(name):
    palette = ("#7e57c2", "#26a69a", "#ef6c00", "#d81b60", "#3949ab", "#43a047")
    color = palette[sum(map(ord, name or "?")) % len(palette)]
    letter = (name or "?")[:1].upper()
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'><rect width='48' height='48' rx='12' "
           f"fill='{color}'/><text x='24' y='32' font-size='24' font-family='sans-serif' fill='white' "
           f"text-anchor='middle'>{letter}</text></svg>")
    return "data:image/svg+xml;utf8," + svg.replace("#", "%23")


class HarnessInfo(QObject):
    """Exposed to the QML stubs as the `Harness` context object."""
    screensChanged = Signal()

    def __init__(self, shell_dir, screens, parent=None):
        super().__init__(parent)
        self._shell_dir, self._screens = shell_dir, screens

    @Slot(str, str, result=str)
    @Slot(str, bool, result=str)
    def iconPath(self, name, fallback):
        # iconPath(name, true) is Quickshell's "check" form: empty when the theme lacks the icon.
        if fallback is True or fallback is False:
            found = find_icon(name)
            return "file://" + found if found else ""
        found = find_icon(name) or find_icon(fallback)
        return "file://" + found if found else placeholder_icon(name)

    shellDir = Property(str, lambda s: s._shell_dir, constant=True)
    screens = Property("QVariantList", lambda s: list(s._screens), notify=screensChanged)


_registered = {}


def _singleton(cls, uri, name, key):
    """Register a per-engine singleton; the live instance is kept in `_registered`."""
    def create(engine):
        _registered[key] = cls()
        return _registered[key]
    qmlRegisterSingletonType(cls, uri, 1, 0, name, create)


class Services:
    """Handles to the live stub singletons of the current engine."""

    @property
    def hyprland(self):
        return _registered["hyprland"]

    @property
    def tray(self):
        return _registered["tray"]

    @property
    def mpris(self):
        return _registered["mpris"]


_types_registered = False


def register(info):
    """Register every stub type once per process; singletons are rebuilt per engine."""
    global _types_registered
    NotificationServer.instances.clear()
    Process.log.clear()
    if not _types_registered:
        _types_registered = True
        qmlRegisterType(Process, "Quickshell.Io", 1, 0, "Process")
        qmlRegisterType(StdioCollector, "Quickshell.Io", 1, 0, "StdioCollector")
        qmlRegisterType(SplitParser, "Quickshell.Io", 1, 0, "SplitParser")
        qmlRegisterType(IpcHandler, "Quickshell.Io", 1, 0, "IpcHandler")
        qmlRegisterType(HyprlandFocusGrab, "Quickshell.Hyprland", 1, 0, "HyprlandFocusGrab")
        qmlRegisterType(NotificationServer, "Quickshell.Services.Notifications", 1, 0, "NotificationServer")
        _singleton(HyprlandIpc, "Quickshell.Hyprland", "Hyprland", "hyprland")
        _singleton(SystemTrayService, "Quickshell.Services.SystemTray", "SystemTray", "tray")
        _singleton(MprisService, "Quickshell.Services.Mpris", "Mpris", "mpris")
    return Services()
