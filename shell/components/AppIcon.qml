import QtQuick
import Quickshell
import "../services"

// Application icon from the installed icon theme. An app whose icon the theme does
// not have gets a tonal letter tile instead of the generic "executable" art, so the
// launcher, dock and Recents never show a mismatched placeholder.
Item {
    id: root
    property string icon: ""
    property string label: ""
    readonly property string path: icon.length > 0 ? Quickshell.iconPath(icon, true) : ""
    readonly property bool found: path.length > 0
    readonly property string initial: {
        const letters = label.match(/[A-Za-z0-9]/);
        return letters ? letters[0].toUpperCase() : "?";
    }
    // The same app always gets the same tone.
    readonly property var tone: {
        // Solid tones, so the tile stands out on both the dock and the launcher.
        const tones = [[Theme.primary, Theme.primaryInk], [Theme.secondary, Theme.secondaryInk], [Theme.tertiary, Theme.tertiaryInk], [Theme.inverseSurface, Theme.inverseSurfaceInk]];
        let sum = 0;
        for (let i = 0; i < label.length; i++)
            sum += label.charCodeAt(i);
        return tones[sum % tones.length];
    }
    implicitWidth: 40
    implicitHeight: 40
    Image {
        anchors.fill: parent
        visible: root.found
        source: root.path
        sourceSize: Qt.size(Math.max(1, Math.ceil(root.width * 2)), Math.max(1, Math.ceil(root.height * 2)))
        fillMode: Image.PreserveAspectFit
        asynchronous: true
        smooth: true
        cache: true
    }
    Rectangle {
        anchors.fill: parent
        visible: !root.found
        radius: width * 0.3
        color: root.tone[0]
        Text {
            anchors.centerIn: parent
            text: root.initial
            color: root.tone[1]
            font.family: Theme.font
            font.pixelSize: Math.round(root.height * 0.5)
            font.weight: Font.DemiBold
            renderType: Text.QtRendering
        }
    }
}
