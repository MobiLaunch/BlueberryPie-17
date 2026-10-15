import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../../components"
import "../../services"
import "../../services/Units.js" as Units

// Unit converter: pick a kind, two units, and type a value either side.
ColumnLayout {
    id: root
    property string kind: "length"
    property string from: "m"
    property string to: "ft"
    property string amount: "1"
    readonly property real result: Units.convert(kind, amount, from, to)
    function pick(id) {
        kind = id;
        const names = Units.unitNames(id);
        from = names[0 + (id === "length" ? 2 : 0)];
        to = names[Math.min(names.length - 1, id === "length" ? 5 : 1)];
    }
    function swap() {
        const converted = result;
        const previous = from;
        from = to;
        to = previous;
        if (isFinite(converted))
            amount = Units.format(converted);
    }
    spacing: 12
    Flow {
        Layout.fillWidth: true
        spacing: 8
        Repeater {
            model: Units.CATEGORIES
            delegate: FilterChip {
                required property var modelData
                text: modelData.title
                selected: root.kind === modelData.id
                onClicked: root.pick(modelData.id)
            }
        }
    }
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: fromColumn.implicitHeight + 28
        radius: Theme.shape.extraLarge
        color: Theme.surfaceContainer
        ColumnLayout {
            id: fromColumn
            anchors.fill: parent
            anchors.margins: 14
            spacing: 8
            Label {
                text: "From"
                role: "labelLarge"
                color: Theme.surfaceVariantInk
            }
            ExpressiveTextField {
                Layout.fillWidth: true
                text: root.amount
                inputMethodHints: Qt.ImhFormattedNumbersOnly
                placeholderText: "Amount"
                Accessible.name: "Amount to convert"
                onTextEdited: root.amount = text
            }
            Flow {
                Layout.fillWidth: true
                spacing: 6
                Repeater {
                    model: Units.unitNames(root.kind)
                    delegate: FilterChip {
                        required property string modelData
                        text: modelData
                        implicitHeight: 34
                        selected: root.from === modelData
                        onClicked: root.from = modelData
                    }
                }
            }
        }
    }
    IconButton {
        Layout.alignment: Qt.AlignHCenter
        symbol: "arrow"
        rotation: 90
        variant: "tonal"
        Accessible.name: "Swap units"
        onClicked: root.swap()
    }
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: toColumn.implicitHeight + 28
        radius: Theme.shape.extraLarge
        color: Theme.primaryContainer
        ColumnLayout {
            id: toColumn
            anchors.fill: parent
            anchors.margins: 14
            spacing: 8
            Label {
                text: "To"
                role: "labelLarge"
                color: Theme.primaryContainerInk
            }
            Label {
                Layout.fillWidth: true
                text: isFinite(root.result) ? Units.format(root.result) + " " + root.to : root.amount.length > 0 ? "Enter a valid number" : ""
                role: "headlineMedium"
                color: Theme.primaryContainerInk
                elide: Text.ElideRight
            }
            Flow {
                Layout.fillWidth: true
                spacing: 6
                Repeater {
                    model: Units.unitNames(root.kind)
                    delegate: FilterChip {
                        required property string modelData
                        text: modelData
                        implicitHeight: 34
                        selected: root.to === modelData
                        onClicked: root.to = modelData
                    }
                }
            }
        }
    }
    Item {
        Layout.fillHeight: true
    }
}
