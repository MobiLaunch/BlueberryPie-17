import QtQuick
import "../components"
import "../services"

Label {
    id: root
    property color ink: Theme.wallpaperInk
    property real size: 120
    property date now: new Date()
    text: Theme.timeText(now)
    font.pixelSize: size
    font.weight: Font.Black
    font.letterSpacing: -size * 0.05
    color: ink
    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: root.now = new Date()
    }
}
