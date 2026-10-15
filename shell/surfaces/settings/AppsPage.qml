import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    title: "Apps"
    SettingsGroup {
        width: parent.width
        ListRow {
            width: parent.width
            title: "Installed apps"
            supporting: SystemBridge.apps.length + " on this device"
            symbol: "apps_grid"
            onClicked: ShellState.toggleDrawer(ShellState.focusedScreen())
        }
        ListRow {
            width: parent.width
            title: "Prism Store"
            supporting: "Find and install Linux and Android apps"
            symbol: "store"
            onClicked: ShellState.openStore(ShellState.focusedScreen())
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Android apps"
        ToggleRow {
            width: parent.width
            title: "Run Android apps"
            supporting: "Games and apps alongside Linux windows"
            symbol: "android"
            on: AndroidState.enabled
            enabled: !AndroidState.busy
            onSwitched: value => AndroidState.setEnabled(value)
        }
    }
    Row {
        visible: AndroidState.enabled
        width: parent.width
        spacing: 12
        leftPadding: 16
        ExpressiveLoader {
            width: 32
            height: 32
            visible: AndroidState.busy
            color: Theme.primary
        }
        Label {
            width: parent.width - 60 - (AndroidState.busy ? 44 : 0)
            text: AndroidState.label
            role: "bodyMedium"
            wrapMode: Text.WordWrap
            anchors.verticalCenter: parent.verticalCenter
        }
    }
    Label {
        width: parent.width
        visible: AndroidState.error.length > 0
        leftPadding: 16
        wrapMode: Text.WordWrap
        color: Theme.error
        text: AndroidState.error
    }
    Flow {
        width: parent.width
        spacing: 10
        leftPadding: 4
        visible: AndroidState.enabled && !AndroidState.busy
        PillButton {
            text: "Retry setup"
            variant: "tonal"
            visible: !AndroidState.ready
            onClicked: AndroidState.setEnabled(true)
        }
        PillButton {
            text: AndroidState.fdroidInstalled ? "Open F-Droid" : "Install F-Droid"
            variant: "filled"
            visible: AndroidState.ready
            onClicked: AndroidState.fdroidInstalled ? AndroidState.openFdroid() : AndroidState.installFdroid()
        }
        PillButton {
            text: "Open Android"
            variant: "tonal"
            visible: AndroidState.ready
            onClicked: AndroidState.openAndroid()
        }
    }
    Label {
        width: parent.width
        leftPadding: 16
        rightPadding: 16
        text: "Optional. Downloads the Android system image on first use; an administrator may need to approve setup. Turning this off never deletes your Android data. F-Droid is installed only when you request it."
        role: "bodySmall"
        color: Theme.surfaceVariantInk
        wrapMode: Text.WordWrap
    }
}
