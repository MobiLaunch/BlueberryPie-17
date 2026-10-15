import QtQuick
import QtQuick.Controls
import "."
import "../services"

// A ListRow with a switch. `on` is authoritative state from the system;
// the switch flips optimistically on click and snaps back to `checked` if the
// system does not confirm within a moment.
ListRow {
    id: root
    property bool on: false
    signal switched(bool value)
    onClicked: {
        if (!enabled)
            return;
        toggle.checked = !toggle.checked;
        root.switched(toggle.checked);
        settle.restart();
    }
    Timer {
        id: settle
        interval: 1600
        onTriggered: toggle.checked = root.on
    }
    onOnChanged: toggle.checked = on
    AndroidToggle {
        id: toggle
        checked: root.on
        enabled: root.enabled
        Accessible.name: root.title
        // The row is the click target; the switch only displays state.
        onClicked: {
            root.switched(checked);
            settle.restart();
        }
    }
}
