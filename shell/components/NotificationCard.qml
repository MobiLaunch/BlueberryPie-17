import QtQuick
import QtQuick.Layouts
import Quickshell.Services.Notifications
import "../services"

Rectangle {
    id: root
    required property var notification
    readonly property bool critical: notification.urgency === NotificationUrgency.Critical
    implicitHeight: message.implicitHeight + 32
    radius: 24
    color: Theme.surface
    border.width: critical ? 2 : 0
    border.color: Theme.roles.error
    ColumnLayout {
        id: message
        x: 16
        y: 16
        width: parent.width - 62
        spacing: 6
        Label {
            Layout.fillWidth: true
            text: root.notification.appName + (root.critical ? " • Important" : "")
            font.pixelSize: 11
            font.weight: Font.DemiBold
            elide: Text.ElideRight
        }
        Label {
            Layout.fillWidth: true
            text: root.notification.summary
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
        }
        Label {
            Layout.fillWidth: true
            text: root.notification.body
            font.pixelSize: 12
            wrapMode: Text.WordWrap
            maximumLineCount: 5
            elide: Text.ElideRight
            visible: text.length > 0
        }
        Flow {
            Layout.fillWidth: true
            spacing: 5
            Repeater {
                model: root.notification.actions
                delegate: PillButton {
                    required property var modelData
                    text: modelData.text || "Open"
                    implicitHeight: 36
                    filled: true
                    onClicked: modelData.invoke()
                }
            }
        }
    }
    PillButton {
        anchors.right: parent.right
        anchors.rightMargin: 6
        y: 8
        text: "×"
        implicitWidth: 38
        implicitHeight: 38
        Accessible.name: "Dismiss " + root.notification.summary
        onClicked: root.notification.dismiss()
    }
}
