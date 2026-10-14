import QtQuick
import QtQuick.Layouts
import "../services"

Rectangle {
    id: root
    property var player: MediaState.player
    implicitHeight: 154
    radius: 28
    color: Theme.secondary
    visible: player !== null
    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 14
        Rectangle {
            Layout.preferredWidth: 64
            Layout.preferredHeight: 64
            radius: 22
            color: Theme.primary
            Image {
                anchors.fill: parent
                anchors.margins: 5
                source: root.player ? root.player.trackArtUrl : ""
                fillMode: Image.PreserveAspectFit
                visible: status === Image.Ready
                sourceSize: Qt.size(128, 128)
            }
            Symbol {
                anchors.centerIn: parent
                width: 28
                height: 28
                name: "music"
                color: Theme.onPrimary
                visible: !root.player || !root.player.trackArtUrl
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 5
            Label {
                Layout.fillWidth: true
                text: root.player ? root.player.identity : ""
                font.pixelSize: 11
                color: Theme.onSecondary
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                text: root.player ? (root.player.trackTitle || "Now playing") : ""
                font.pixelSize: 16
                font.weight: Font.DemiBold
                color: Theme.onSecondary
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                text: root.player ? root.player.trackArtist : ""
                font.pixelSize: 12
                color: Theme.onSecondary
                elide: Text.ElideRight
            }
            RowLayout {
                spacing: 5
                PillButton {
                    text: "‹"
                    Accessible.name: "Previous track"
                    implicitWidth: 44
                    implicitHeight: 38
                    enabled: root.player && root.player.canGoPrevious
                    onClicked: root.player.previous()
                }
                PillButton {
                    text: root.player && root.player.isPlaying ? "Ⅱ" : "▶"
                    Accessible.name: root.player && root.player.isPlaying ? "Pause" : "Play"
                    filled: true
                    implicitWidth: 48
                    implicitHeight: 38
                    enabled: root.player && root.player.canTogglePlaying
                    onClicked: root.player.togglePlaying()
                }
                PillButton {
                    text: "›"
                    Accessible.name: "Next track"
                    implicitWidth: 44
                    implicitHeight: 38
                    enabled: root.player && root.player.canGoNext
                    onClicked: root.player.next()
                }
                PillButton {
                    text: "↻"
                    Accessible.name: "Switch media player"
                    implicitWidth: 38
                    implicitHeight: 38
                    visible: MediaState.players.length > 1
                    onClicked: MediaState.cycle()
                }
            }
        }
    }
}
