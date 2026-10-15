import QtQuick
import "../components"
import "../services"

// The Quick Settings media card, placed on the desktop while a player exists.
MediaCard {
    width: 360
    height: visible ? implicitHeight : 0
}
