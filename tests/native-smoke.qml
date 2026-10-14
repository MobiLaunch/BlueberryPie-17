import QtQuick
import Quickshell
import Quickshell.Services.SystemTray
import "../shell/components"
import "../shell/services"

ShellRoot {
    property QtObject fakePlayer: QtObject {
        property string identity: "Smoke player"
        property string trackTitle: "A colorful test"
        property string trackArtist: "Prism"
        property string trackArtUrl: ""
        property bool isPlaying: false
        property bool canTogglePlaying: true
        property bool canGoNext: false
        property bool canGoPrevious: false
        function togglePlaying() {
            isPlaying = !isPlaying;
        }
    }
    property QtObject fakeAction: QtObject {
        property string text: "Open test"
        property bool invoked: false
        function invoke() {
            invoked = true;
        }
    }
    property QtObject fakeNote: QtObject {
        property string appName: "Prism test"
        property string summary: "Native notification"
        property string body: "<b>This stays plain text</b>"
        property int urgency: 1
        property var actions: [fakeAction]
        function dismiss() {
        }
    }
    FloatingWindow {
        implicitWidth: 420
        implicitHeight: 580
        visible: true
        color: Theme.surface
        Column {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12
            QuickTile {
                width: parent.width
                title: "Native tile"
                subtitle: "Ready"
                activated: true
            }
            ExpressiveSlider {
                width: parent.width
                value: 50
            }
            MediaCard {
                width: parent.width
                player: fakePlayer
            }
            NotificationCard {
                width: parent.width
                notification: fakeNote
            }
            ExpressiveLoader {
                width: 40
                height: 40
            }
        }
        AppMenu {
            app: ({
                    id: "fixture.desktop",
                    name: "Fixture"
                })
        }
    }
    Timer {
        property int attempts: 0
        interval: 200
        running: true
        repeat: true
        onTriggered: {
            attempts++;
            if (Applications.dockApps.length === 1 && Theme.roles.primary) {
                fakePlayer.togglePlaying();
                fakeAction.invoke();
                if (!fakePlayer.isPlaying || !fakeAction.invoked || Notifications.items.values === undefined || MediaState.players === undefined || SystemTray.items.values === undefined) {
                    console.error("PRISM_NATIVE_SMOKE_FAILED");
                    Qt.exit(1);
                    return;
                }
                ShellState.focusedScreen();
                console.info("PRISM_NATIVE_SMOKE_OK");
                Qt.quit();
            } else if (attempts >= 25) {
                console.error("PRISM_NATIVE_SMOKE_FAILED: bridge or favorites did not load");
                Qt.exit(1);
            }
        }
    }
}
