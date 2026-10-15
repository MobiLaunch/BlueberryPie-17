import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Services.Notifications
import "."
import "../services"

// One notification. Swipe sideways to dismiss; critical ones use the error
// container. Actions are the sender's own, never synthesized.
Item {
    id: root
    required property var notification
    property bool compact: false
    readonly property bool critical: notification.urgency === NotificationUrgency.Critical
    implicitHeight: card.implicitHeight
    clip: false

    function dismiss(direction) {
        leave.to = direction * (root.width + 40);
        leave.start();
    }
    NumberAnimation {
        id: leave
        target: card
        property: "x"
        duration: Theme.fast
        onFinished: root.notification.dismiss()
    }
    NumberAnimation {
        id: snapBack
        target: card
        property: "x"
        to: 0
        duration: Theme.standard
        easing.type: Easing.OutBack
    }
    Rectangle {
        id: card
        width: parent.width
        implicitHeight: body.implicitHeight + 28
        height: implicitHeight
        radius: Theme.shape.extraLarge - 6
        color: root.critical ? Theme.errorContainer : Theme.surfaceContainerHighest
        opacity: 1 - Math.min(0.7, Math.abs(x) / Math.max(1, root.width))
        DragHandler {
            id: swipe
            yAxis.enabled: false
            xAxis.minimum: -root.width
            xAxis.maximum: root.width
            onActiveChanged: {
                if (active)
                    return;
                if (Math.abs(card.x) > root.width * 0.33)
                    root.dismiss(card.x > 0 ? 1 : -1);
                else
                    snapBack.restart();
            }
        }
        RowLayout {
            id: body
            x: 14
            y: 14
            width: parent.width - 28
            spacing: 12
            Rectangle {
                Layout.alignment: Qt.AlignTop
                Layout.preferredWidth: 40
                Layout.preferredHeight: 40
                radius: 20
                color: root.critical ? Theme.error : Theme.tertiaryContainer
                clip: true
                Image {
                    id: appIcon
                    anchors.centerIn: parent
                    width: 26
                    height: 26
                    sourceSize: Qt.size(52, 52)
                    source: Quickshell.iconPath(root.notification.appIcon || root.notification.desktopEntry || "", true)
                    visible: source.toString().length > 0 && status === Image.Ready
                }
                Symbol {
                    anchors.centerIn: parent
                    width: 22
                    height: 22
                    visible: !appIcon.visible
                    name: root.critical ? "info" : "notifications"
                    color: root.critical ? Theme.errorInk : Theme.tertiaryContainerInk
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    Layout.fillWidth: true
                    text: root.notification.appName + (root.critical ? " · Important" : "")
                    role: "labelMedium"
                    color: root.critical ? Theme.errorContainerInk : Theme.surfaceVariantInk
                    elide: Text.ElideRight
                }
                Label {
                    Layout.fillWidth: true
                    text: root.notification.summary
                    role: "titleSmall"
                    color: root.critical ? Theme.errorContainerInk : Theme.surfaceInk
                    wrapMode: Text.WordWrap
                    maximumLineCount: 2
                    elide: Text.ElideRight
                }
                Label {
                    Layout.fillWidth: true
                    visible: text.length > 0 && !root.compact
                    text: root.notification.body
                    role: "bodyMedium"
                    color: root.critical ? Theme.errorContainerInk : Theme.surfaceVariantInk
                    wrapMode: Text.WordWrap
                    maximumLineCount: 4
                    elide: Text.ElideRight
                }
                Flow {
                    Layout.fillWidth: true
                    Layout.topMargin: 4
                    spacing: 6
                    visible: root.notification.actions.length > 0 && !root.compact
                    Repeater {
                        model: root.notification.actions
                        delegate: PillButton {
                            required property var modelData
                            text: modelData.text || "Open"
                            variant: "tonal"
                            implicitHeight: 36
                            onClicked: modelData.invoke()
                        }
                    }
                }
            }
            IconButton {
                Layout.alignment: Qt.AlignTop
                implicitWidth: 36
                implicitHeight: 36
                iconSize: 18
                symbol: "close"
                Accessible.name: "Dismiss " + root.notification.summary
                onClicked: root.dismiss(1)
            }
        }
    }
}
