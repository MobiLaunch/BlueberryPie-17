import QtQuick
import QtQuick.Controls
import "."
import "../services"

// Shared button. `variant`: filled | tonal | neutral | outlined | text.
// Shape morphs from fully rounded to a squarer corner while pressed.
// Padding is explicit so labels are never clipped by a style's defaults.
Button {
    id: root
    property bool filled: false
    property string variant: filled ? "filled" : "neutral"
    property string symbol: ""
    readonly property color containerColor: variant === "filled" ? Theme.primary : variant === "tonal" ? Theme.secondaryContainer : variant === "neutral" ? Theme.surfaceContainerHigh : "transparent"
    readonly property color contentColor: variant === "filled" ? Theme.primaryInk : variant === "tonal" ? Theme.secondaryContainerInk : variant === "text" || variant === "outlined" ? Theme.primary : Theme.surfaceInk
    leftPadding: text.length > 0 ? (symbol ? 16 : 20) : 12
    rightPadding: text.length > 0 ? 20 : 12
    topPadding: 0
    bottomPadding: 0
    readonly property real iconSpace: symbol.length > 0 && text.length > 0 ? 28 : symbol.length > 0 ? 20 : 0
    // Measured independently of the Label so width never depends on itself.
    readonly property real labelWidth: text.length > 0 ? Math.ceil(metrics.advanceWidth) + 1 : 0
    implicitWidth: Math.max(48, iconSpace + labelWidth + leftPadding + rightPadding)
    implicitHeight: 48
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: text
    scale: down ? 0.97 : 1
    Behavior on scale {
        NumberAnimation {
            duration: Theme.fast
            easing.type: Easing.OutBack
        }
    }
    TextMetrics {
        id: metrics
        text: root.text
        font: measuredLabel.font
    }
    background: Rectangle {
        radius: root.down ? Theme.shape.large : height / 2
        color: root.containerColor
        opacity: root.enabled ? 1 : 0.38
        border.width: root.visualFocus ? 2 : root.variant === "outlined" ? 1 : 0
        border.color: root.visualFocus ? Theme.primary : Theme.outline
        Behavior on radius {
            NumberAnimation {
                duration: Theme.fast
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
            tint: root.contentColor
            hovered: root.hovered && root.enabled
            pressed: root.down
            focused: root.visualFocus
        }
    }
    contentItem: Item {
        implicitWidth: content.implicitWidth
        implicitHeight: content.implicitHeight
        Row {
            id: content
            anchors.centerIn: parent
            spacing: 8
            opacity: root.enabled ? 1 : 0.38
            Symbol {
                visible: root.symbol.length > 0
                anchors.verticalCenter: parent.verticalCenter
                width: 20
                height: 20
                name: root.symbol
                color: root.contentColor
            }
            Label {
                id: measuredLabel
                visible: root.text.length > 0
                anchors.verticalCenter: parent.verticalCenter
                text: root.text
                role: "labelLarge"
                color: root.contentColor
                elide: Text.ElideRight
                width: Math.min(root.labelWidth, Math.max(0, root.availableWidth - (root.symbol.length > 0 ? 28 : 0)))
            }
        }
    }
}
