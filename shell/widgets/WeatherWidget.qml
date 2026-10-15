import QtQuick
import "../components"
import "../services"

WidgetCard {
    id: root
    readonly property var data: WidgetsState.weather
    readonly property bool ready: WidgetsState.weatherConfigured && data.ok === true && data.temperature !== undefined
    widgetId: "weather"
    Column {
        width: parent.width
        spacing: 6
        Row {
            spacing: 14
            Symbol {
                visible: root.ready
                anchors.verticalCenter: parent.verticalCenter
                width: 56
                height: 56
                name: root.ready ? root.data.icon : "cloud"
                color: Theme.primary
            }
            Column {
                anchors.verticalCenter: parent.verticalCenter
                Label {
                    visible: root.ready
                    text: root.ready ? root.data.temperature + "°" : ""
                    role: "displaySmall"
                    font.weight: Font.DemiBold
                }
                Label {
                    text: root.ready ? root.data.summary : WidgetsState.weatherConfigured ? "Weather is unavailable right now" : "No place chosen"
                    role: root.ready ? "titleMedium" : "bodyLarge"
                    width: root.width - root.padding * 2 - (root.ready ? 70 : 0)
                    wrapMode: Text.WordWrap
                }
            }
        }
        Label {
            visible: root.ready
            width: parent.width
            text: root.ready ? "High " + root.data.high + "° · Low " + root.data.low + "° · Feels like " + root.data.feels_like + "°" : ""
            role: "bodyMedium"
            color: Theme.surfaceVariantInk
        }
        Label {
            visible: WidgetsState.weatherConfigured
            width: parent.width
            text: WidgetsState.place.label || ""
            role: "labelMedium"
            color: Theme.surfaceVariantInk
            elide: Text.ElideRight
        }
        PillButton {
            visible: !WidgetsState.weatherConfigured
            text: "Choose a place"
            variant: "tonal"
            onClicked: ShellState.openSettings(ShellState.focusedScreen(), "widgets")
        }
    }
}
