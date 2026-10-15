import QtQuick
import QtQuick.Layouts
import "../components"
import "../services"

// Shown only on the live USB: a way into the installer that never gets in the way.
WidgetCard {
    id: root
    property var screen: null
    padding: 14
    RowLayout {
        width: parent.width
        spacing: 12
        Rectangle {
            Layout.preferredWidth: 48
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignVCenter
            radius: 16
            color: Theme.primaryContainer
            Symbol {
                anchors.centerIn: parent
                width: 26
                height: 26
                name: "download"
                color: Theme.primaryContainerInk
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Label {
                Layout.fillWidth: true
                text: "Install PrismOS"
                role: "titleMedium"
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                text: "Running from the USB drive"
                role: "bodySmall"
                color: Theme.surfaceVariantInk
                elide: Text.ElideRight
            }
        }
        PillButton {
            text: "Install"
            variant: "filled"
            implicitHeight: 40
            onClicked: ShellState.openInstaller(root.screen)
        }
    }
}
