import QtQuick
import "../components"
import "../services"
import "../widgets"

// Widgets placed on the wallpaper layer. The first column is text on the
// wallpaper; cards flow below it and hide on short screens rather than overlap the dock.
Item {
    id: root
    property var screen: null
    property color ink: Theme.wallpaperInk
    readonly property real gutter: Math.max(40, width * .075)
    readonly property real headroom: Math.max(76, height * .11)
    Column {
        id: column
        x: root.gutter
        y: root.headroom
        spacing: 10
        GlanceWidget {
            visible: WidgetsState.has("glance")
            ink: root.ink
        }
        ClockWidget {
            visible: WidgetsState.has("clock")
            ink: root.ink
            size: Math.min(130, root.width * .12)
        }
        InstallerWidget {
            visible: InstallerState.live
            screen: root.screen
            width: Math.min(440, root.width - root.gutter * 2)
        }
        SearchWidget {
            visible: WidgetsState.has("search")
            screen: root.screen
            width: Math.min(440, root.width - root.gutter * 2)
        }
    }
    Flow {
        x: root.gutter
        y: column.y + column.height + 28
        width: root.width - root.gutter * 2
        spacing: 16
        visible: root.height >= 720
        CalendarWidget {
            visible: WidgetsState.has("calendar")
        }
        WeatherWidget {
            visible: WidgetsState.has("weather")
        }
        SystemWidget {
            visible: WidgetsState.has("system")
        }
        NotesWidget {
            visible: WidgetsState.has("notes")
        }
        AnalogClockWidget {
            visible: WidgetsState.has("analog")
        }
        MediaWidget {
            visible: WidgetsState.has("media") && MediaState.player !== null
        }
    }
}
