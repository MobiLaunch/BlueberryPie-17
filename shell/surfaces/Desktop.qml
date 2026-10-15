import QtQuick
import Quickshell

// Everything PrismOS draws on one screen. Panels are separate layer-shell
// surfaces so each can take focus and animate independently.
Scope {
    id: root
    required property var modelData
    property var screen: modelData
    Wallpaper {
        screen: root.screen
    }
    StatusBar {
        screen: root.screen
    }
    Dock {
        screen: root.screen
    }
    QuickSettings {
        screen: root.screen
    }
    AppDrawer {
        screen: root.screen
    }
    PrismStore {
        screen: root.screen
    }
    Files {
        screen: root.screen
    }
    Utilities {
        screen: root.screen
    }
    Settings {
        screen: root.screen
    }
    FirstRun {
        screen: root.screen
    }
    Installer {
        screen: root.screen
    }
    Recents {
        screen: root.screen
    }
    LaunchSplash {
        screen: root.screen
    }
    PowerMenu {
        screen: root.screen
    }
    AppInfo {
        screen: root.screen
    }
    HeadsUp {
        screen: root.screen
    }
    AlarmRinging {
        screen: root.screen
    }
    Osd {
        screen: root.screen
    }
    Toast {
        screen: root.screen
    }
}
