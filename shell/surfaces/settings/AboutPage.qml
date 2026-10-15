import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "About"
    readonly property var info: AboutState.info
    Component.onCompleted: AboutState.refresh()
    Rectangle {
        width: parent.width
        height: 132
        radius: Theme.shape.extraLargeIncreased
        color: Theme.primaryContainer
        Rectangle {
            x: 24
            anchors.verticalCenter: parent.verticalCenter
            width: 72
            height: 72
            radius: 24
            color: Theme.primary
            Symbol {
                anchors.centerIn: parent
                width: 40
                height: 40
                name: "spark"
                color: Theme.primaryInk
            }
        }
        Column {
            x: 116
            anchors.verticalCenter: parent.verticalCenter
            Label {
                text: "PrismOS"
                role: "headlineSmallEmphasized"
                color: Theme.primaryContainerInk
            }
            Label {
                text: "Version " + (page.info.prismos || "—") + " · Arch Linux"
                role: "bodyLarge"
                color: Theme.primaryContainerInk
            }
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Device"
        ListRow {
            width: parent.width
            interactive: false
            title: "Device name"
            supporting: page.info.hostname || "—"
        }
        ListRow {
            width: parent.width
            interactive: false
            title: "Processor"
            supporting: page.info.cpu || "Unknown"
        }
        ListRow {
            width: parent.width
            interactive: false
            title: "Memory"
            supporting: page.info.memory_gib ? page.info.memory_gib + " GiB" : "Unknown"
        }
        ListRow {
            width: parent.width
            interactive: false
            title: "Storage"
            supporting: page.info.storage ? page.info.storage.free_gib + " GiB free of " + page.info.storage.total_gib + " GiB" : "Unknown"
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Software"
        ListRow {
            width: parent.width
            interactive: false
            title: "Base system"
            supporting: page.info.base || "—"
        }
        ListRow {
            width: parent.width
            interactive: false
            title: "Kernel"
            supporting: page.info.kernel || "—"
        }
        ListRow {
            width: parent.width
            interactive: false
            title: "Session"
            supporting: (page.info.desktop || "PrismOS") + (page.info.session ? " · " + page.info.session : "")
        }
        ListRow {
            width: parent.width
            interactive: false
            title: "Uptime"
            supporting: AboutState.duration(page.info.uptime_seconds)
        }
    }
}
