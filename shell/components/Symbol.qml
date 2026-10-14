import QtQuick
import "../services"
import "IconData.js" as IconData

// Stroke icon recolored by rewriting the SVG, so it follows the theme on any
// renderer (no shader effects) and tints instantly when roles change.
Item {
    id: root
    property string name: "spark"
    property color color: Theme.onSurface
    property real weight: 1.9
    // 0..1 fill for the battery glyph; ignored by other symbols.
    property real level: -1
    implicitWidth: 24
    implicitHeight: 24
    readonly property string baseMarkup: IconData.paths[name] || IconData.paths["spark"]
    readonly property string markup: level >= 0 && name === "battery" ? baseMarkup.replace("width=\"12\"", "width=\"" + Math.max(1.4, 12 * Math.min(1, level)) + "\"") : baseMarkup
    readonly property string svg: {
        const ink = Theme.hex(color);
        return "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='" + ink + "' stroke-opacity='" + color.a + "' stroke-width='" + weight + "' stroke-linecap='round' stroke-linejoin='round'>" + markup.replace(/#19151e/g, ink).replace(/"/g, "'") + "</svg>";
    }
    Image {
        anchors.fill: parent
        source: "data:image/svg+xml;utf8," + encodeURIComponent(root.svg)
        sourceSize: Qt.size(Math.max(1, Math.ceil(root.width * 2)), Math.max(1, Math.ceil(root.height * 2)))
        fillMode: Image.PreserveAspectFit
        smooth: true
        cache: true
    }
}
