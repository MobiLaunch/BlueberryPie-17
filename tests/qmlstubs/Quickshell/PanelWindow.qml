import QtQuick
import Quickshell.Wayland

// Layer-shell panel approximation: an Item placed on the shared desk by its
// anchors, margins and implicit size. It does not model focus, input regions
// or exclusive zones; those need a real compositor.
QtObject {
    id: win
    default property alias data: contentRoot.data
    property var screen: Harness.screens.length ? Harness.screens[0] : null
    property PanelAnchors anchors: PanelAnchors {}
    property PanelMargins margins: PanelMargins {}
    property int exclusionMode: 0
    property int exclusiveZone: 0
    property real implicitWidth: 0
    property real implicitHeight: 0
    property real width: contentRoot.width
    property real height: contentRoot.height
    property color color: "white"
    property bool visible: true
    property bool focusable: true
    // Attached properties must be read on the window object itself.
    readonly property int layerZ: WlrLayershell.layer
    property Region mask: null
    readonly property real screenWidth: screen ? screen.width : 1280
    readonly property real screenHeight: screen ? screen.height : 800

    property Item contentItem: Item {
        id: contentRoot
        visible: win.visible
        parent: HarnessDesk.item
        width: win.anchors.left && win.anchors.right ? win.screenWidth - win.margins.left - win.margins.right : win.implicitWidth
        height: win.anchors.top && win.anchors.bottom ? win.screenHeight - win.margins.top - win.margins.bottom : win.implicitHeight
        x: win.anchors.left ? win.margins.left : win.anchors.right ? win.screenWidth - width - win.margins.right : (win.screenWidth - width) / 2
        y: win.anchors.top ? win.margins.top : win.anchors.bottom ? win.screenHeight - height - win.margins.bottom : (win.screenHeight - height) / 2
        z: win.layerZ
        Rectangle {
            anchors.fill: parent
            color: win.color
            z: -1000
        }
    }
}
