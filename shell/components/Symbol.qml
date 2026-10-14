import QtQuick
import QtQuick.Effects
import Quickshell
import "../services"

Item {
    id: root
    property string name: "spark"
    property color color: Theme.onSurfaceHigh
    implicitWidth: 24
    implicitHeight: 24
    Image {
        anchors.fill: parent
        source: Quickshell.shellPath("../design/icons/" + root.name + ".svg")
        sourceSize: Qt.size(root.width * 2, root.height * 2)
        fillMode: Image.PreserveAspectFit
        smooth: true
        layer.enabled: true
        layer.effect: MultiEffect {
            colorization: 1
            colorizationColor: root.color
        }
    }
}
