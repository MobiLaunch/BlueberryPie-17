pragma Singleton
import QtQuick
import Quickshell.Services.Mpris

QtObject {
    property string selectedId: ""
    readonly property var players: Mpris.players.values
    readonly property var player: players.find(item => item.dbusName === selectedId) || players.find(item => item.isPlaying) || players[0] || null
    function cycle() {
        if (players.length < 2)
            return;
        const index = players.indexOf(player);
        selectedId = players[(index + 1) % players.length].dbusName;
    }
}
