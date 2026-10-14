import QtQuick
import QtQuick.Controls
import "../services"

Switch {
    id: root
    implicitWidth: 66
    implicitHeight: 42
    hoverEnabled: true
    Accessible.name: "Enable Android apps"
    padding: 0
    spacing: 0
    indicator: Rectangle {
        implicitWidth: 64
        implicitHeight: 36
        x: root.leftPadding
        y: (root.height - height) / 2
        radius: height / 2
        color: root.checked ? Theme.primaryStrong : Theme.surfaceHigh
        border.width: root.checked ? 0 : 2
        border.color: Theme.outline
        opacity: root.enabled ? 1 : .45
        Behavior on color { ColorAnimation { duration: Theme.fast } }
        Rectangle {
            width: root.checked ? 28 : 20
            height: root.checked ? 28 : 20
            radius: height / 2
            x: root.checked ? parent.width - width - 4 : 8
            anchors.verticalCenter: parent.verticalCenter
            color: root.checked ? Theme.onPrimaryStrong : Theme.onSurfaceHigh
            Behavior on x {
                NumberAnimation { duration: Theme.standard; easing.type: Easing.OutBack }
            }
            Behavior on width { NumberAnimation { duration: Theme.fast } }
            Behavior on height { NumberAnimation { duration: Theme.fast } }
        }
    }
    contentItem: Item {}
}
