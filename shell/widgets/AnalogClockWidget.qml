import QtQuick
import "../components"
import "../services"

// A cookie-dial analog clock in the current palette.
Item {
    id: root
    property date now: new Date()
    implicitWidth: 220
    implicitHeight: 220
    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: root.now = new Date()
    }
    Image {
        anchors.fill: parent
        sourceSize: Qt.size(440, 440)
        source: "data:image/svg+xml;utf8," + encodeURIComponent(root.dial)
    }
    readonly property string dial: {
        const points = [];
        for (let i = 0; i <= 240; i++) {
            const angle = i * Math.PI / 120;
            const radius = 92 + 8 * Math.cos(angle * 12);
            points.push((100 + Math.cos(angle) * radius).toFixed(1) + "," + (100 + Math.sin(angle) * radius).toFixed(1));
        }
        return "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'><polygon points='" + points.join(" ") + "' fill='" + Theme.hex(Theme.primaryContainer) + "'/></svg>";
    }
    component Hand: Rectangle {
        property real turns
        property real reach
        property color tone: Theme.primaryContainerInk
        x: root.width / 2 - width / 2
        y: root.height / 2 - reach
        height: reach
        radius: width / 2
        color: tone
        transformOrigin: Item.Bottom
        rotation: turns * 360
    }
    Hand {
        width: 10
        reach: 54
        turns: ((root.now.getHours() % 12) + root.now.getMinutes() / 60) / 12
    }
    Hand {
        width: 7
        reach: 78
        turns: (root.now.getMinutes() + root.now.getSeconds() / 60) / 60
    }
    Hand {
        width: 3
        reach: 84
        tone: Theme.primary
        turns: root.now.getSeconds() / 60
    }
    Rectangle {
        anchors.centerIn: parent
        width: 16
        height: 16
        radius: 8
        color: Theme.primary
    }
}
