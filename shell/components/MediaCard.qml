import QtQuick
import QtQuick.Layouts
import "."
import "../services"

// Now-playing card driven by MPRIS. Controls are enabled only when the player
// advertises the capability.
Rectangle {
    id: root
    property var player: MediaState.player
    implicitHeight: 128
    radius: Theme.shape.extraLarge
    color: Theme.secondaryContainer
    visible: player !== null
    RowLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 14
        Rectangle {
            Layout.preferredWidth: 88
            Layout.preferredHeight: 88
            Layout.alignment: Qt.AlignVCenter
            radius: Theme.shape.largeIncreased
            color: Theme.primaryContainer
            clip: true
            Image {
                anchors.fill: parent
                source: root.player ? root.player.trackArtUrl : ""
                fillMode: Image.PreserveAspectCrop
                visible: status === Image.Ready
                sourceSize: Qt.size(176, 176)
            }
            Symbol {
                anchors.centerIn: parent
                width: 36
                height: 36
                name: "music"
                color: Theme.primaryContainerInk
                visible: !root.player || !root.player.trackArtUrl
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter
            spacing: 2
            Label {
                Layout.fillWidth: true
                text: root.player ? root.player.identity : ""
                role: "labelMedium"
                color: Theme.secondaryContainerInk
                opacity: 0.8
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                text: root.player ? (root.player.trackTitle || "Now playing") : ""
                role: "titleMedium"
                color: Theme.secondaryContainerInk
                elide: Text.ElideRight
            }
            Label {
                Layout.fillWidth: true
                text: root.player ? root.player.trackArtist : ""
                role: "bodySmall"
                color: Theme.secondaryContainerInk
                opacity: 0.85
                elide: Text.ElideRight
            }
            RowLayout {
                Layout.topMargin: 4
                spacing: 2
                IconButton {
                    symbol: "skip_previous"
                    implicitWidth: 40
                    implicitHeight: 40
                    iconSize: 22
                    Accessible.name: "Previous track"
                    enabled: root.player && root.player.canGoPrevious
                    onClicked: root.player.previous()
                }
                IconButton {
                    symbol: root.player && root.player.isPlaying ? "pause" : "play"
                    variant: "filled"
                    implicitWidth: 48
                    implicitHeight: 40
                    iconSize: 22
                    Accessible.name: root.player && root.player.isPlaying ? "Pause" : "Play"
                    enabled: root.player && root.player.canTogglePlaying
                    onClicked: root.player.togglePlaying()
                }
                IconButton {
                    symbol: "skip_next"
                    implicitWidth: 40
                    implicitHeight: 40
                    iconSize: 22
                    Accessible.name: "Next track"
                    enabled: root.player && root.player.canGoNext
                    onClicked: root.player.next()
                }
                IconButton {
                    symbol: "refresh"
                    implicitWidth: 40
                    implicitHeight: 40
                    iconSize: 20
                    visible: MediaState.players.length > 1
                    Accessible.name: "Switch media player"
                    onClicked: MediaState.cycle()
                }
            }
        }
    }
}
