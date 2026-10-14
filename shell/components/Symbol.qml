import QtQuick
import QtQuick.Effects
import Quickshell
import "../services"

Image {
    id: root
    property string name: "spark"
    property color color: Theme.onSurfaceHigh
    source: Quickshell.shellPath("../design/icons/" + name + ".svg")
    sourceSize: Qt.size(width * 2, height * 2)
    fillMode: Image.PreserveAspectFit
    smooth: true
    layer.enabled: true
    layer.effect: MultiEffect {
        colorization: 1
        colorizationColor: root.color
    }
}
