pragma Singleton
import QtQuick

// Parent for every PanelWindow content item so the whole desktop can be
// composited and captured. Quickshell itself gives each panel its own surface.
QtObject {
    property Item item: null
}
