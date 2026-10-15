import QtQuick
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "Storage"
    readonly property var usage: StorageState.usage
    readonly property real total: usage.total || 0
    readonly property var colors: ({
            documents: Theme.primary,
            downloads: Theme.tertiary,
            pictures: Theme.secondary,
            music: Theme.inversePrimary,
            videos: Theme.primaryContainer,
            apps: Theme.tertiaryContainer,
            cache: Theme.secondaryContainer,
            other: Theme.outline
        })
    Component.onCompleted: StorageState.refresh()
    Rectangle {
        width: parent.width
        height: 168
        radius: Theme.shape.extraLargeIncreased
        color: Theme.primaryContainer
        objectName: "storage-summary"
        Column {
            anchors.verticalCenter: parent.verticalCenter
            x: 24
            width: parent.width - 48
            spacing: 12
            Label {
                text: page.total > 0 ? StorageState.size(page.usage.used) + " used" : "Reading storage…"
                role: "headlineMedium"
                color: Theme.primaryContainerInk
            }
            Label {
                width: parent.width
                text: page.total > 0 ? StorageState.size(page.usage.free) + " free of " + StorageState.size(page.total) : ""
                role: "bodyLarge"
                color: Theme.primaryContainerInk
                wrapMode: Text.WordWrap
            }
            Rectangle {
                id: bar
                objectName: "storage-bar"
                width: parent.width
                height: 16
                radius: 8
                color: Theme.surfaceContainerHighest
                clip: true
                Row {
                    height: parent.height
                    spacing: 2
                    Repeater {
                        model: page.total > 0 ? page.usage.items : []
                        Rectangle {
                            required property var modelData
                            height: bar.height
                            width: modelData.bytes > 0 ? Math.max(4, bar.width * modelData.bytes / page.total) : 0
                            color: page.colors[modelData.id] || Theme.outline
                        }
                    }
                }
            }
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Your files"
        Repeater {
            model: page.total > 0 ? page.usage.items : []
            ListRow {
                required property var modelData
                width: parent.width
                interactive: false
                visible: modelData.bytes > 0
                objectName: "storage-" + modelData.id
                title: modelData.label
                supporting: StorageState.size(modelData.bytes)
                symbol: "folder"
                chipColor: page.colors[modelData.id] || Theme.outline
                chipInk: Theme.surfaceInk
            }
        }
        ListRow {
            width: parent.width
            interactive: false
            visible: page.total > 0 && page.usage.yours === 0
            title: "No files counted yet"
            supporting: "Your home folder is empty."
            symbol: "folder"
        }
    }
    Label {
        width: parent.width
        visible: StorageState.error.length > 0 || page.usage.truncated === true
        leftPadding: 16
        rightPadding: 16
        wrapMode: Text.WordWrap
        role: "bodyMedium"
        color: StorageState.error.length > 0 ? Theme.error : Theme.surfaceVariantInk
        text: StorageState.error.length > 0 ? StorageState.error : "Your folder is very large, so these sizes are a partial count."
    }
    SettingsGroup {
        width: parent.width
        title: "Free up space"
        ListRow {
            width: parent.width
            objectName: "storage-clear-previews"
            symbol: "trash"
            title: "Clear window previews"
            supporting: StorageState.size(page.usage.previews || 0) + " in Recents previews. They are re-created when you open Recents."
            enabled: !StorageState.busy && (page.usage.previews || 0) > 0
            onClicked: StorageState.clearPreviews()
        }
        ListRow {
            width: parent.width
            objectName: "storage-refresh"
            symbol: "refresh"
            title: "Recount"
            supporting: "Measure your folders again"
            enabled: !StorageState.busy
            onClicked: StorageState.refresh()
        }
    }
}
