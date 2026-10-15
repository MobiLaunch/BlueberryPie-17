import QtQuick
import "../components"
import "../services"

// Date plus the most useful single fact: weather if set up, otherwise battery,
// otherwise a greeting. Text only, drawn straight on the wallpaper.
Column {
    id: root
    property color ink: Theme.wallpaperInk
    property string dateText: Qt.formatDate(new Date(), "dddd, MMMM d")
    readonly property var battery: SystemBridge.snapshot.battery
    readonly property var weather: WidgetsState.weather
    readonly property bool hasWeather: WidgetsState.weatherConfigured && weather.ok === true && weather.temperature !== undefined
    readonly property int hour: new Date().getHours()
    readonly property string greeting: hour < 5 ? "Good night" : hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening"
    spacing: 4
    Timer {
        interval: 60000
        running: true
        repeat: true
        onTriggered: root.dateText = Qt.formatDate(new Date(), "dddd, MMMM d")
    }
    Label {
        text: root.dateText
        role: "headlineSmall"
        color: root.ink
    }
    Row {
        spacing: 8
        Symbol {
            anchors.verticalCenter: parent.verticalCenter
            width: 22
            height: 22
            visible: root.hasWeather || root.battery.available
            name: root.hasWeather ? root.weather.icon : (root.battery.charging ? "battery_charging" : "battery")
            level: !root.hasWeather && root.battery.available ? root.battery.value / 100 : -1
            color: root.ink
        }
        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: root.hasWeather ? root.weather.temperature + "°  ·  " + root.weather.summary + "  ·  " + root.weather.label : root.battery.available ? "Battery " + root.battery.value + "%" + (root.battery.charging ? " · Charging" : "") : root.greeting
            role: "titleMedium"
            color: root.ink
            opacity: 0.9
        }
    }
}
