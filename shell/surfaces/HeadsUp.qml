import QtQuick
import Quickshell
import Quickshell.Wayland
import "../components"
import "../services"

// Banner for a newly arrived notification. It can be swiped away, acted on, or
// left to time out; the full list always remains in the shade.
PanelWindow {
    id: root
    readonly property var note: Notifications.headsUp
    anchors.top: true
    margins.top: 52
    implicitWidth: Math.min(440, screen.width - 24)
    implicitHeight: banner.height + 12
    exclusionMode: ExclusionMode.Ignore
    WlrLayershell.namespace: "prism-headsup"
    color: "transparent"
    visible: note !== null && !ShellState.shadeOpen && ShellState.activeScreen === screen
    Item {
        id: banner
        width: parent.width
        height: card.implicitHeight
        y: root.visible ? 0 : -24
        Behavior on y {
            NumberAnimation {
                duration: Theme.standard
                easing.type: Easing.OutBack
            }
        }
        Loader {
            id: card
            width: parent.width
            active: root.note !== null
            property real implicitHeight: item ? item.implicitHeight : 0
            sourceComponent: NotificationCard {
                notification: root.note
                // The banner window never takes keyboard focus, so replies are typed in the shade.
                allowReply: false
            }
        }
    }
}
