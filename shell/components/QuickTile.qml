import QtQuick
import QtQuick.Controls
import "."
import "../services"

// Quick Settings tile. `large` tiles show title and state; compact tiles show
// only the icon (the name is its tooltip and accessible label).
// Active = pill, inactive = squircle, pressed = tighter corner (Android 12+).
Button {
    id: root
    property string title: ""
    property string subtitle: ""
    property string symbol: "spark"
    property bool activated: false
    property bool large: true
    property bool hasDetails: false
    // Looks unavailable but still takes input (so its details can explain why).
    property bool dimmed: false
    readonly property real fade: enabled && !dimmed ? 1 : 0.5
    // With large text the chevron gives way to the label; press and hold or right-click still opens details.
    readonly property bool showChevron: hasDetails && Theme.fontScale <= 1.1
    signal detailsRequested
    implicitWidth: large ? 176 : 84
    implicitHeight: 72
    leftPadding: 0
    rightPadding: 0
    topPadding: 0
    bottomPadding: 0
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: title + (subtitle ? ", " + subtitle : "")
    Accessible.checkable: true
    Accessible.checked: activated
    ToolTip.visible: !large && hovered
    ToolTip.delay: 500
    ToolTip.text: title + (subtitle ? " · " + subtitle : "")
    scale: down ? 0.97 : 1
    Behavior on scale {
        NumberAnimation {
            duration: Theme.fast
            easing.type: Easing.OutBack
        }
    }
    readonly property color inkColor: activated ? Theme.primaryInk : Theme.surfaceInk
    background: Rectangle {
        radius: root.down ? Theme.shape.large : root.activated ? height / 2 : Theme.shape.extraLarge - 4
        color: root.activated ? Theme.primary : Theme.surfaceContainerHighest
        opacity: root.fade
        border.width: root.visualFocus ? 2 : 0
        border.color: Theme.primary
        Behavior on radius {
            NumberAnimation {
                duration: Theme.standard
                easing.type: Easing.OutBack
                easing.overshoot: 1.2
            }
        }
        Behavior on color {
            ColorAnimation {
                duration: Theme.fast
            }
        }
        StateLayer {
            anchors.fill: parent
            radius: parent.radius
            tint: root.inkColor
            hovered: root.hovered && root.enabled
            pressed: root.down
            focused: root.visualFocus
        }
    }
    contentItem: Item {
        Symbol {
            x: root.large ? 20 : (parent.width - width) / 2
            y: (parent.height - height) / 2
            width: 24
            height: 24
            name: root.symbol
            filled: root.activated
            color: root.inkColor
            opacity: root.fade
        }
        Column {
            visible: root.large
            x: 56
            y: (parent.height - height) / 2
            width: Math.max(0, parent.width - 56 - (root.showChevron ? 46 : 14))
            spacing: 1
            opacity: root.fade
            Label {
                width: parent.width
                text: root.title
                role: "titleSmall"
                color: root.inkColor
                elide: Text.ElideRight
            }
            Label {
                width: parent.width
                visible: text.length > 0
                text: root.subtitle
                role: "bodySmall"
                color: root.inkColor
                opacity: 0.85
                elide: Text.ElideRight
            }
        }
        Rectangle {
            visible: root.large && root.showChevron
            anchors.right: parent.right
            anchors.rightMargin: 8
            anchors.verticalCenter: parent.verticalCenter
            width: 34
            height: 34
            radius: 17
            color: Theme.withAlpha(root.inkColor, detailsArea.containsMouse ? 0.16 : 0.08)
            Symbol {
                anchors.centerIn: parent
                width: 18
                height: 18
                name: "arrow"
                color: root.inkColor
            }
            MouseArea {
                id: detailsArea
                anchors.fill: parent
                anchors.margins: -6
                hoverEnabled: true
                enabled: root.enabled
                cursorShape: Qt.PointingHandCursor
                Accessible.role: Accessible.Button
                Accessible.name: root.title + " details"
                onClicked: root.detailsRequested()
            }
        }
    }
    onPressAndHold: if (hasDetails)
        detailsRequested()
    TapHandler {
        acceptedButtons: Qt.RightButton
        enabled: root.hasDetails
        onTapped: root.detailsRequested()
    }
}
