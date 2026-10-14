import QtQuick
import "../services"

// Material state layer: hover, keyboard focus and press tint drawn over a
// shaped container. Parent supplies the interaction state.
Rectangle {
    id: root
    property bool hovered: false
    property bool pressed: false
    property bool focused: false
    property color tint: Theme.onSurface
    color: tint
    opacity: pressed ? 0.12 : focused ? 0.12 : hovered ? 0.08 : 0
    Behavior on opacity {
        NumberAnimation {
            duration: Theme.fast
        }
    }
}
