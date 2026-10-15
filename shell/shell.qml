import QtQuick
import Quickshell
import Quickshell.Io
import "services"
import "surfaces"

ShellRoot {
    Component.onCompleted: {
        SystemBridge.refresh();
        InstallerState.probe();
        console.info("PrismOS 0.9 shell started");
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
        function files(): void {
            ShellState.openFiles(ShellState.focusedScreen());
        }
        function store(): void {
            ShellState.openStore(ShellState.focusedScreen());
        }
        function installer(): void {
            ShellState.openInstaller(ShellState.focusedScreen());
        }
        function screenshot(): void {
            ShellState.screenshot("area");
        }
        function screenshotFull(): void {
            ShellState.screenshot("full");
        }
        function calculator(): void {
            ShellState.openUtilities(ShellState.focusedScreen(), "calculator");
        }
        function clock(): void {
            ShellState.openUtilities(ShellState.focusedScreen(), "timer");
        }
        function alarms(): void {
            ShellState.openUtilities(ShellState.focusedScreen(), "alarms");
        }
        function clipboard(): void {
            ShellState.openUtilities(ShellState.focusedScreen(), "clipboard");
        }
        function worldclock(): void {
            ShellState.openUtilities(ShellState.focusedScreen(), "world");
        }
        function converter(): void {
            ShellState.openUtilities(ShellState.focusedScreen(), "converter");
        }
        function recents(): void {
            ShellState.toggleRecents(ShellState.focusedScreen());
        }
        function power(): void {
            ShellState.openPower(ShellState.focusedScreen());
        }
        function record(): void {
            ShellState.toggleRecording();
        }
        function volumeUp(): void {
            if (SystemBridge.step("volume", 5))
                ShellState.showOsd("volume");
        }
        function volumeDown(): void {
            if (SystemBridge.step("volume", -5))
                ShellState.showOsd("volume");
        }
        function volumeMute(): void {
            SystemBridge.action("mute");
            if (SystemBridge.snapshot.volume.available)
                ShellState.showOsd("volume");
        }
        function micMute(): void {
            SystemBridge.action("microphone-mute");
            if (SystemBridge.snapshot.microphone.available)
                ShellState.showOsd("microphone");
        }
        function brightnessUp(): void {
            if (SystemBridge.step("brightness", 5))
                ShellState.showOsd("brightness");
        }
        function brightnessDown(): void {
            if (SystemBridge.step("brightness", -5))
                ShellState.showOsd("brightness");
        }
        function close(): void {
            ShellState.close();
        }
    }
}
