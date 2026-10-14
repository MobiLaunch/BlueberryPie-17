import QtQuick
import Quickshell

// Shared surface that every stub PanelWindow draws onto.
Rectangle {
    id: desk
    color: "#101010"
    Component.onCompleted: HarnessDesk.item = desk
}
