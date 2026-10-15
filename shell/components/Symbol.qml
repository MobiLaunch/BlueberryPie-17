import QtQuick
import "../services"
import "IconData.js" as IconData

// Material Symbols (Rounded) glyph, recolored by rewriting the SVG so it follows the
// theme on any renderer (no shader effects) and tints instantly when roles change.
// `filled` switches to the filled variant, used for active and selected states.
Item {
    id: root
    property string name: "spark"
    property color color: Theme.surfaceInk
    property bool filled: false
    // 0..1 charge for the battery glyph; ignored by other symbols.
    property real level: -1
    implicitWidth: 24
    implicitHeight: 24
    // The battery has real glyphs for seven partial levels plus full.
    readonly property string resolved: {
        if (name === "battery" && level >= 0 && level < 0.97)
            return "battery_level_" + Math.min(6, Math.floor(level * 7));
        return name;
    }
    readonly property string pathData: (filled ? IconData.filled : IconData.outline)[resolved] || IconData.outline["spark"]
    readonly property string svg: "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 -960 960 960'><path fill='" + Theme.hex(color) + "' fill-opacity='" + color.a + "' d='" + pathData + "'/></svg>"
    Image {
        anchors.fill: parent
        source: "data:image/svg+xml;utf8," + encodeURIComponent(root.svg)
        sourceSize: Qt.size(Math.max(1, Math.ceil(root.width * 2)), Math.max(1, Math.ceil(root.height * 2)))
        fillMode: Image.PreserveAspectFit
        smooth: true
        cache: true
    }
}
