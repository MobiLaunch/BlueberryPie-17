import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// On-screen indicator for the hardware volume, microphone and brightness keys. It is
// non-interactive (the input region is empty), follows the focused screen and fades after
// a moment; the level is the bridge's predicted value, so it moves with every key press.
PanelWindow {
    id: root
    readonly property bool active: ShellState.osdKind.length > 0 && ShellState.osdScreen === screen
    readonly property string kind: ShellState.osdKind || lastKind
    property string lastKind: "volume"
    readonly property var snap: SystemBridge.snapshot
    readonly property bool isVolume: kind === "volume"
    readonly property bool isMic: kind === "microphone"
    readonly property bool muted: isVolume ? snap.volume.muted : isMic ? snap.microphone.muted : false
    readonly property real level: isVolume ? snap.volume.value : isMic ? snap.microphone.value : snap.brightness.value
    readonly property string title: isVolume ? "Volume" : isMic ? "Microphone" : "Brightness"
    readonly property string glyph: {
        if (isMic)
            return muted ? "microphone_off" : "microphone";
        if (isVolume)
            return muted || level <= 0 ? "volume_off" : level < 35 ? "volume_down" : "volume";
        return "brightness";
    }
    onActiveChanged: if (active)
        lastKind = ShellState.osdKind
    anchors.bottom: true
    // Above the snackbar when a failed command is also reporting an error.
    margins.bottom: ShellState.toast.length > 0 ? 184 : 112
    implicitWidth: Math.min(Math.round(360 * Math.max(1, Theme.fontScale)), screen.width - 40)
    implicitHeight: pill.height + 8
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-osd"
    color: "transparent"
    mask: Region {}
    visible: active || pill.opacity > 0.01
    Rectangle {
        id: pill
        objectName: "osd-pill"
        width: parent.width
        height: 68
        radius: height / 2
        color: Theme.surfaceContainerHigh
        border.width: 1
        border.color: Theme.withAlpha(Theme.outlineVariant, 0.7)
        opacity: root.active ? 1 : 0
        scale: root.active ? 1 : 0.94
        Behavior on opacity {
            NumberAnimation {
                duration: Theme.fast
            }
        }
        Behavior on scale {
            NumberAnimation {
                duration: Theme.standard
                easing.type: Easing.OutBack
                easing.overshoot: .6
            }
        }
        Accessible.role: Accessible.StaticText
        Accessible.name: root.title + (root.muted ? " muted" : " " + Math.round(root.level) + " percent")
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: 20
            anchors.rightMargin: 24
            spacing: 14
            Rectangle {
                Layout.preferredWidth: 44
                Layout.preferredHeight: 44
                radius: 22
                color: root.muted ? Theme.errorContainer : Theme.primaryContainer
                Symbol {
                    anchors.centerIn: parent
                    width: 26
                    height: 26
                    name: root.glyph
                    filled: true
                    color: root.muted ? Theme.errorContainerInk : Theme.primaryContainerInk
                }
            }
            LinearProgress {
                Layout.fillWidth: true
                value: root.muted ? 0 : root.level / 100
            }
            Label {
                objectName: "osd-value"
                Layout.preferredWidth: Math.round(46 * Math.max(1, Theme.fontScale))
                horizontalAlignment: Text.AlignRight
                text: root.muted ? "Muted" : Math.round(root.level) + "%"
                role: "labelLarge"
                color: Theme.surfaceInk
            }
        }
    }
}
