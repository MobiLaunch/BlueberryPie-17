import QtQuick
import QtQuick.Layouts
import "../components"
import "../services"

// Month grid with today highlighted; arrows browse, the heading returns to today.
WidgetCard {
    id: root
    property date today: new Date()
    property int year: today.getFullYear()
    property int month: today.getMonth()
    readonly property int firstDay: Qt.locale().firstDayOfWeek % 7
    readonly property int offset: (new Date(year, month, 1).getDay() - firstDay + 7) % 7
    readonly property int days: new Date(year, month + 1, 0).getDate()
    readonly property int rows: Math.ceil((offset + days) / 7)
    readonly property var dayNames: {
        const names = [];
        for (let i = 0; i < 7; i++)
            names.push(Qt.locale().dayName((firstDay + i) % 7, Locale.ShortFormat).charAt(0).toUpperCase());
        return names;
    }
    implicitWidth: 292
    function shift(delta) {
        const next = new Date(year, month + delta, 1);
        year = next.getFullYear();
        month = next.getMonth();
    }
    Timer {
        interval: 60000
        running: true
        repeat: true
        onTriggered: root.today = new Date()
    }
    Column {
        width: parent.width
        spacing: 6
        RowLayout {
            width: parent.width
            spacing: 2
            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 6
                text: Qt.locale().monthName(root.month) + " " + root.year
                role: "titleMedium"
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    Accessible.role: Accessible.Button
                    Accessible.name: "Show this month"
                    onClicked: {
                        root.today = new Date();
                        root.year = root.today.getFullYear();
                        root.month = root.today.getMonth();
                    }
                }
            }
            IconButton {
                symbol: "back"
                implicitWidth: 36
                implicitHeight: 36
                iconSize: 18
                Accessible.name: "Previous month"
                onClicked: root.shift(-1)
            }
            IconButton {
                symbol: "arrow"
                implicitWidth: 36
                implicitHeight: 36
                iconSize: 18
                Accessible.name: "Next month"
                onClicked: root.shift(1)
            }
        }
        Row {
            Repeater {
                model: root.dayNames
                delegate: Label {
                    required property string modelData
                    width: (root.width - root.padding * 2) / 7
                    horizontalAlignment: Text.AlignHCenter
                    text: modelData
                    role: "labelMedium"
                    color: Theme.surfaceVariantInk
                }
            }
        }
        Grid {
            columns: 7
            Repeater {
                model: root.rows * 7
                delegate: Item {
                    required property int index
                    readonly property int day: index - root.offset + 1
                    readonly property bool inMonth: day >= 1 && day <= root.days
                    readonly property bool isToday: inMonth && root.year === root.today.getFullYear() && root.month === root.today.getMonth() && day === root.today.getDate()
                    width: (root.width - root.padding * 2) / 7
                    height: 32
                    Rectangle {
                        anchors.centerIn: parent
                        width: 30
                        height: 30
                        radius: 15
                        color: isToday ? Theme.primary : "transparent"
                    }
                    Label {
                        anchors.centerIn: parent
                        text: inMonth ? day : ""
                        role: "labelLarge"
                        color: isToday ? Theme.primaryInk : Theme.surfaceInk
                        font.weight: isToday ? Font.Bold : Font.Medium
                    }
                }
            }
        }
    }
}
