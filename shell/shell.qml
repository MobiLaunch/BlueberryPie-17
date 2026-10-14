import QtQuick
import Quickshell
import Quickshell.Io
import "services"
import "surfaces"

ShellRoot {
    Component.onCompleted: {
        SystemBridge.refresh();
        console.info("PrismOS 0.1 shell started");
    }
    Variants {
        model: Quickshell.screens
        delegate: Desktop {}
    }
    IpcHandler {
        target: "prism"
        function shade(): void {
            ShellState.toggleShade(ShellState.activeScreen);
        }
        function launcher(): void {
            ShellState.toggleDrawer(ShellState.activeScreen);
        }
        function settings(): void {
            ShellState.openSettings(ShellState.activeScreen);
        }
        function close(): void {
            ShellState.close();
        }
    }
}
