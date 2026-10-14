import QtQuick
import "../services"

// Themed text. Set `role` to a Material 3 type-scale name (for example
// "titleMedium") to take size, weight, tracking and line height from Theme.type.
Text {
    property string role: ""
    readonly property var spec: role ? Theme.type[role] : null
    color: Theme.onSurface
    font.family: Theme.font
    font.pixelSize: spec ? spec.size : 14
    font.weight: spec ? spec.weight : Font.Normal
    font.letterSpacing: spec ? spec.tracking : 0
    lineHeight: spec ? spec.line : 1
    lineHeightMode: spec ? Text.FixedHeight : Text.ProportionalHeight
    textFormat: Text.PlainText
    renderType: Text.QtRendering
}
