"""Quickshell.Wayland layer-shell attached properties.

The WlrLayer / WlrKeyboardFocus enums are QML singletons under
tests/qmlstubs/Quickshell/Wayland.
"""
from PySide6.QtCore import Property, QObject, Signal
from PySide6.QtQml import QmlAttached, QmlElement

QML_IMPORT_NAME = "Quickshell.Wayland"
QML_IMPORT_MAJOR_VERSION = 1


class LayerAttached(QObject):
    layerChanged = Signal()
    namespaceChanged = Signal()
    keyboardFocusChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layer, self._namespace, self._focus = 2, "", 0

    def _set(self, name, value, signal):
        setattr(self, name, value)
        signal.emit()

    layer = Property(int, lambda s: s._layer, lambda s, v: s._set("_layer", int(v), s.layerChanged),
                     notify=layerChanged)
    namespace = Property(str, lambda s: s._namespace, lambda s, v: s._set("_namespace", v, s.namespaceChanged),
                         notify=namespaceChanged)
    keyboardFocus = Property(int, lambda s: s._focus, lambda s, v: s._set("_focus", int(v), s.keyboardFocusChanged),
                             notify=keyboardFocusChanged)


@QmlElement
@QmlAttached(LayerAttached)
class WlrLayershell(QObject):
    @staticmethod
    def qmlAttachedProperties(*args):
        return LayerAttached(args[-1])
