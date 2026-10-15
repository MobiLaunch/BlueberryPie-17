import QtQuick
import QtQuick.Layouts
import "."
import "../services"

// Card with a title, live value text and an Expressive slider.
Rectangle {
    id: root
    property alias title: heading.text
    property alias symbol: slider.symbol
    property alias modelValue: slider.modelValue
    property alias from: slider.from
    property alias to: slider.to
    property alias stepSize: slider.stepSize
    property alias keyStep: slider.keyStep
    property string valueText: Math.round(slider.value) + "%"
    property string supporting: ""
    signal committed(real level)
    implicitHeight: body.implicitHeight + 28
    radius: Theme.shape.extraLarge - 4
    color: Theme.surfaceContainer
    ColumnLayout {
        id: body
        x: 16
        y: 14
        width: parent.width - 32
        spacing: 6
        RowLayout {
            Layout.fillWidth: true
            Label {
                id: heading
                Layout.fillWidth: true
                role: "bodyLarge"
            }
            Label {
                text: root.valueText
                role: "labelLarge"
                color: Theme.surfaceVariantInk
            }
        }
        Label {
            Layout.fillWidth: true
            visible: text.length > 0
            text: root.supporting
            role: "bodyMedium"
            color: Theme.surfaceVariantInk
            wrapMode: Text.WordWrap
        }
        ExpressiveSlider {
            id: slider
            Layout.fillWidth: true
            label: heading.text
            // The header already shows the value, in this row's own units.
            showValue: false
            onCommitted: level => root.committed(level)
        }
    }
}
