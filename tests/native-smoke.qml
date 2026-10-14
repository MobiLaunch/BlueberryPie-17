import QtQuick
import Quickshell
import Quickshell.Services.SystemTray
import "../shell/components"
import "../shell/services"

ShellRoot {
    id: smokeRoot
    property int sliderLevel: 50
    Component.onCompleted: {
        const output = {
            id: 42,
            serial: "1042",
            name: "fixture-speakers",
            label: "Fixture speakers",
            kind: "output",
            selected: true,
            available: true,
            value: 64,
            muted: false
        };
        const input = {
            id: 54,
            serial: "1054",
            name: "fixture-mic",
            label: "Fixture microphone",
            kind: "input",
            selected: true,
            available: true,
            value: 48,
            muted: true
        };
        AudioState.devices = {
            available: true,
            outputs: [output],
            inputs: [input],
            output: output,
            input: input
        };
        Wireless.wifi = ({
                available: true,
                enabled: true,
                networks: [
                    {
                        bssid: "AA:BB:CC:DD:EE:FF",
                        interface: "wlan0",
                        ssid: "Smoke network",
                        signal: 84,
                        secured: true,
                        supported: true,
                        connected: false,
                        profile: null,
                        key: "wpa-psk"
                    }
                ]
            });
        Wireless.bluetooth = ({
                available: true,
                enabled: true,
                devices: [
                    {
                        address: "AA:BB:CC:DD:EE:01",
                        name: "Smoke buds",
                        paired: true,
                        connected: true
                    }
                ]
            });
    }
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
                id: smokeSlider
                width: parent.width
                modelValue: smokeRoot.sliderLevel
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
            WirelessPanel {
                width: parent.width
                kind: "wifi"
                selected: "AA:BB:CC:DD:EE:FF/wlan0"
            }
            WirelessPanel {
                width: parent.width
                kind: "bluetooth"
            }
            SoundPanel {
                width: parent.width
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
        property int phase: 0
        interval: 200
        running: true
        repeat: true
        onTriggered: {
            attempts++;
            if (Applications.dockApps.length === 1 && Theme.roles.primary) {
                if (phase === 0) {
                    smokeSlider.value = 25;
                    smokeRoot.sliderLevel = 70;
                    AudioState.adjusting = true;
                    AudioState.refresh();
                    if (AudioState.busy || !AudioState.needsRead) {
                        console.error("PRISM_NATIVE_SMOKE_FAILED: sound refresh interrupted a drag");
                        Qt.exit(1);
                        return;
                    }
                    AudioState.adjusting = false;
                    // Exercise the production stdin pipe with a synthetic secret;
                    // the subprocess only asserts input and returns fixture JSON.
                    const accepted = Wireless.execute("wifi", "connect", ["python3", "-c", "import json,sys; assert json.loads(sys.stdin.readline())['password'] == 'fixture secret'; print(json.dumps({'ok':True}))"], "fixture secret");
                    if (!accepted) {
                        console.error("PRISM_NATIVE_SMOKE_FAILED: pipe did not start");
                        Qt.exit(1);
                        return;
                    }
                    ShellState.launching = {
                        id: "fixture.desktop",
                        startupClass: "FixtureWindow"
                    };
                    ShellState.launchMinimumElapsed = false;
                    ShellState.windowArrived("openwindow", "abc,1,Unrelated,Ignore this");
                    if (ShellState.launchReady) {
                        console.error("PRISM_NATIVE_SMOKE_FAILED: unrelated window matched");
                        Qt.exit(1);
                        return;
                    }
                    ShellState.windowArrived("openwindow", "abc,1,FixtureWindow,A title, with commas");
                    if (!ShellState.launchReady || !ShellState.launching) {
                        console.error("PRISM_NATIVE_SMOKE_FAILED: minimum animation was skipped");
                        Qt.exit(1);
                        return;
                    }
                    ShellState.minimumLaunch.interval = 10;
                    ShellState.minimumLaunch.restart();
                    phase = 1;
                    return;
                }
                if (phase === 1) {
                    if (Wireless.busy || AudioState.busy)
                        return;
                    if (smokeSlider.value !== 70 || AudioState.needsRead) {
                        console.error("PRISM_NATIVE_SMOKE_FAILED: slider lost model binding or deferred sound refresh");
                        Qt.exit(1);
                        return;
                    }
                    if (Wireless.secret || Wireless.notice !== "Connected" || ShellState.launching) {
                        console.error("PRISM_NATIVE_SMOKE_FAILED: pipe or window readiness");
                        Qt.exit(1);
                        return;
                    }
                    // Reuse an existing app and then exercise an unmatched-app timeout.
                    ShellState.launching = {
                        id: "fixture.desktop"
                    };
                    ShellState.launchMinimumElapsed = true;
                    ShellState.windowArrived("activewindow", "fixture,Existing title");
                    if (ShellState.launching) {
                        console.error("PRISM_NATIVE_SMOKE_FAILED: existing window not recognized");
                        Qt.exit(1);
                        return;
                    }
                    ShellState.launching = {
                        id: "unmatched.desktop"
                    };
                    ShellState.launchTimer.interval = 10;
                    ShellState.launchTimer.restart();
                    phase = 2;
                    return;
                }
                if (ShellState.launching) {
                    console.error("PRISM_NATIVE_SMOKE_FAILED: timeout left an overlay");
                    Qt.exit(1);
                    return;
                }
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
