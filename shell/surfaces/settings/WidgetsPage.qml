import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../components"
import "../../services"

SettingsPage {
    id: page
    title: "Widgets"
    Component.onCompleted: WidgetsState.places = []
    SettingsGroup {
        width: parent.width
        title: "On your desktop"
        Repeater {
            model: WidgetsState.catalog
            delegate: ToggleRow {
                required property var modelData
                width: parent ? parent.width : 600
                title: modelData.title
                supporting: modelData.description
                symbol: modelData.symbol
                on: WidgetsState.has(modelData.id)
                onSwitched: value => WidgetsState.set(modelData.id, value)
            }
        }
    }
    SettingsGroup {
        width: parent.width
        title: "Weather"
        ListRow {
            width: parent.width
            interactive: false
            visible: WidgetsState.weatherConfigured
            title: WidgetsState.place.label || ""
            supporting: WidgetsState.weather.ok === true ? WidgetsState.weather.temperature + "° · " + WidgetsState.weather.summary : "Fetching…"
            symbol: WidgetsState.weather.ok === true ? WidgetsState.weather.icon : "cloud"
            RowLayout {
                spacing: 6
                FilterChip {
                    text: "°C"
                    selected: WidgetsState.place.units !== "imperial"
                    onClicked: WidgetsState.setUnits("metric")
                }
                FilterChip {
                    text: "°F"
                    selected: WidgetsState.place.units === "imperial"
                    onClicked: WidgetsState.setUnits("imperial")
                }
            }
        }
        ListRow {
            width: parent.width
            visible: WidgetsState.weatherConfigured
            title: "Stop using weather"
            supporting: "Forgets the place and stops all weather requests"
            symbol: "trash"
            onClicked: WidgetsState.disableWeather()
        }
        Rectangle {
            width: parent.width
            height: finder.height + 32
            radius: Theme.shape.extraLarge - 4
            color: Theme.surfaceContainer
            visible: !WidgetsState.weatherConfigured
            property bool interactive: false
            Column {
                id: finder
                x: 16
                y: 16
                width: parent.width - 32
                spacing: 10
                Label {
                    width: parent.width
                    text: "Search for your city"
                    role: "titleMedium"
                }
                RowLayout {
                    width: parent.width
                    spacing: 10
                    ExpressiveTextField {
                        id: cityField
                        Layout.fillWidth: true
                        placeholderText: "For example: Lisbon"
                        maximumLength: 80
                        Accessible.name: "City to search for"
                        onAccepted: searchButton.clicked()
                    }
                    PillButton {
                        id: searchButton
                        text: "Search"
                        variant: "filled"
                        enabled: cityField.text.trim().length >= 2
                        onClicked: WidgetsState.searchPlaces(cityField.text.trim())
                    }
                }
                Label {
                    width: parent.width
                    visible: WidgetsState.searchError.length > 0
                    text: WidgetsState.searchError
                    role: "bodySmall"
                    color: Theme.error
                    wrapMode: Text.WordWrap
                }
                Repeater {
                    model: WidgetsState.places
                    delegate: ListRow {
                        required property var modelData
                        width: finder.width
                        implicitHeight: 56
                        title: modelData.label
                        symbol: "location"
                        onClicked: WidgetsState.choosePlace(modelData, "metric")
                    }
                }
            }
        }
        Label {
            width: parent.width
            leftPadding: 16
            rightPadding: 16
            text: "Weather is optional and off until you choose a place. PrismOS then sends only that place's coordinates to open-meteo.com, over HTTPS, about every 15 minutes while a weather widget is shown."
            role: "bodySmall"
            color: Theme.surfaceVariantInk
            wrapMode: Text.WordWrap
        }
    }
}
