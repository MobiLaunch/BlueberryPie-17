import QtQuick
import Quickshell.Wayland

// Live contents of one window through screencopy. Loaded on demand (see Recents) so a
// Quickshell built without screencopy support only loses live previews, not the overview.
ScreencopyView {
    property var source: null
    captureSource: source
    live: true
}
