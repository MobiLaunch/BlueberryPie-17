import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "Software update"
    readonly property var pacman: UpdateState.info.pacman
    readonly property var flatpak: UpdateState.info.flatpak
    Component.onCompleted: UpdateState.refresh()
    Rectangle {
        width: parent.width
        height: 148
        radius: Theme.shape.extraLargeIncreased
        color: UpdateState.total > 0 ? Theme.tertiaryContainer : Theme.primaryContainer
        objectName: "update-summary"
        Column {
            anchors.verticalCenter: parent.verticalCenter
            x: 24
            width: parent.width - 48
            spacing: 6
            Label {
                width: parent.width
                objectName: "update-headline"
                text: UpdateState.checking ? "Checking…" : UpdateState.summary
                role: "headlineMedium"
                color: UpdateState.total > 0 ? Theme.tertiaryContainerInk : Theme.primaryContainerInk
                wrapMode: Text.WordWrap
            }
            Label {
                width: parent.width
                text: "Last checked " + UpdateState.ago(UpdateState.checked)
                role: "bodyLarge"
                color: UpdateState.total > 0 ? Theme.tertiaryContainerInk : Theme.primaryContainerInk
            }
        }
    }
    Label {
        width: parent.width
        visible: UpdateState.error.length > 0
        leftPadding: 16
        rightPadding: 16
        text: UpdateState.error
        role: "bodyMedium"
        color: Theme.error
        wrapMode: Text.WordWrap
    }
    SettingsGroup {
        width: parent.width
        title: "Actions"
        ListRow {
            width: parent.width
            objectName: "update-check"
            symbol: "refresh"
            title: "Check for updates"
            supporting: UpdateState.checking ? "Asking the package servers…" : "Nothing is installed by checking"
            enabled: !UpdateState.checking
            onClicked: UpdateState.check()
        }
        ListRow {
            width: parent.width
            objectName: "update-install"
            symbol: "update"
            title: "Install updates"
            supporting: "Opens a terminal so you can see and confirm everything"
            enabled: UpdateState.total > 0
            onClicked: UpdateState.install(page.pacman.count > 0 && page.flatpak.count > 0 ? "all" : page.pacman.count > 0 ? "pacman" : "flatpak")
        }
    }
    SettingsGroup {
        width: parent.width
        title: "System packages"
        visible: page.pacman.available === false || page.pacman.error.length > 0 || page.pacman.count > 0
        ListRow {
            width: parent.width
            interactive: false
            visible: page.pacman.available === false || page.pacman.error.length > 0
            objectName: "update-pacman-note"
            symbol: "warning"
            title: page.pacman.available === false ? "Checking is not set up" : "Could not check"
            supporting: page.pacman.error
        }
        Repeater {
            model: page.pacman.items.slice(0, 12)
            ListRow {
                required property var modelData
                width: parent.width
                interactive: false
                objectName: "update-package"
                title: modelData.name
                supporting: modelData.old + " → " + modelData.new
                symbol: "update"
            }
        }
        ListRow {
            width: parent.width
            interactive: false
            visible: page.pacman.count > 12
            title: "And " + (page.pacman.count - 12) + " more"
            symbol: "more"
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Flatpak apps"
        visible: page.flatpak.error.length > 0 || page.flatpak.count > 0
        ListRow {
            width: parent.width
            interactive: false
            visible: page.flatpak.error.length > 0
            symbol: "warning"
            title: "Could not check"
            supporting: page.flatpak.error
        }
        Repeater {
            model: page.flatpak.items.slice(0, 12)
            ListRow {
                required property var modelData
                width: parent.width
                interactive: false
                objectName: "update-flatpak"
                title: modelData.name
                symbol: "update"
            }
        }
    }
}
