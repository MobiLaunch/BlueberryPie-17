import QtQuick
import Quickshell
import Quickshell.Io
import "services"
import "surfaces"

ShellRoot {
    Component.onCompleted: {
        SystemBridge.refresh();
        console.info("PrismOS 0.4 shell started");
    }
    Variants {
        model: Quickshell.screens
        delegate: Desktop {}
    }
    IpcHandler {
        target: "prism"
        function shade(): void {
            ShellState.toggleShade(ShellState.focusedScreen());
        }
        function launcher(): void {
            ShellState.toggleDrawer(ShellState.focusedScreen());
        }
        function settings(): void {
            ShellState.openSettings(ShellState.focusedScreen());
        }
        function power(): void {
            ShellState.openPower(ShellState.focusedScreen());
        }
        function close(): void {
            ShellState.close();
        }
    }
}
