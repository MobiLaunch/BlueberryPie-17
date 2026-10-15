import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../../components"
import "../../services"
import "../../services/Calculator.js" as Calculator

// Calculator with a scientific row. Expressions are parsed by Calculator.js, never evaluated as code.
ColumnLayout {
    id: root
    property bool scientific: false
    property bool degrees: true
    property real ans: 0
    property string failure: ""
    property var history: []
    readonly property var live: Calculator.evaluate(field.text, {
        degrees: degrees,
        ans: ans
    })
    function focusInput() {
        field.forceActiveFocus();
    }
    function put(text) {
        failure = "";
        field.forceActiveFocus();
        field.insert(field.cursorPosition, text);
    }
    function clearAll() {
        failure = "";
        field.text = "";
        field.forceActiveFocus();
    }
    function backspace() {
        failure = "";
        field.forceActiveFocus();
        field.remove(Math.max(0, field.cursorPosition - 1), field.cursorPosition);
    }
    function equals() {
        const result = Calculator.evaluate(field.text, {
            degrees: degrees,
            ans: ans
        });
        if (!result.ok) {
            failure = result.error;
            return;
        }
        failure = "";
        ans = result.value;
        history = [
            {
                expr: field.text,
                result: Calculator.format(result.value)
            }
        ].concat(history).slice(0, 3);
        field.text = Calculator.format(result.value);
        field.cursorPosition = field.text.length;
    }
    spacing: 10
    Rectangle {
        Layout.fillWidth: true
        implicitHeight: 112
        radius: Theme.shape.extraLarge
        color: Theme.surfaceContainer
        Basic.TextField {
            id: field
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 16
            anchors.topMargin: 14
            height: 44
            leftPadding: 0
            rightPadding: 0
            topPadding: 0
            bottomPadding: 0
            horizontalAlignment: TextInput.AlignRight
            verticalAlignment: TextInput.AlignVCenter
            font.family: Theme.font
            font.pixelSize: Math.round(28 * Theme.fontScale)
            color: Theme.surfaceInk
            selectByMouse: true
            placeholderText: "0"
            placeholderTextColor: Theme.outline
            inputMethodHints: Qt.ImhNoPredictiveText
            Accessible.name: "Expression"
            background: Item {}
            onAccepted: root.equals()
            onTextEdited: root.failure = ""
        }
        Label {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.margins: 16
            anchors.bottomMargin: 12
            horizontalAlignment: Text.AlignRight
            role: "titleMedium"
            text: root.failure.length > 0 ? root.failure : root.live.ok && field.text.trim().length > 0 ? "= " + Calculator.format(root.live.value) : ""
            color: root.failure.length > 0 ? Theme.error : Theme.primary
            elide: Text.ElideLeft
        }
    }
    RowLayout {
        Layout.fillWidth: true
        spacing: 8
        FilterChip {
            text: "Scientific"
            selected: root.scientific
            onClicked: root.scientific = !root.scientific
        }
        FilterChip {
            visible: root.scientific
            text: root.degrees ? "Degrees" : "Radians"
            selected: true
            onClicked: root.degrees = !root.degrees
        }
        Item {
            Layout.fillWidth: true
        }
        Repeater {
            model: root.history
            delegate: FilterChip {
                required property var modelData
                text: modelData.result
                ToolTip.visible: hovered
                ToolTip.text: modelData.expr + " = " + modelData.result
                onClicked: root.put(modelData.result)
            }
        }
    }
    GridLayout {
        Layout.fillWidth: true
        visible: root.scientific
        columns: 5
        columnSpacing: 6
        rowSpacing: 6
        Repeater {
            model: [
                {
                    label: "sin",
                    text: "sin("
                },
                {
                    label: "cos",
                    text: "cos("
                },
                {
                    label: "tan",
                    text: "tan("
                },
                {
                    label: "ln",
                    text: "ln("
                },
                {
                    label: "log",
                    text: "log("
                },
                {
                    label: "√",
                    text: "sqrt("
                },
                {
                    label: "π",
                    text: "pi"
                },
                {
                    label: "e",
                    text: "e"
                },
                {
                    label: "xʸ",
                    text: "^"
                },
                {
                    label: "n!",
                    text: "!"
                }
            ]
            delegate: PillButton {
                required property var modelData
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                implicitHeight: 40
                variant: "neutral"
                text: modelData.label
                onClicked: root.put(modelData.text)
            }
        }
    }
    GridLayout {
        Layout.fillWidth: true
        columns: 4
        columnSpacing: 8
        rowSpacing: 8
        Repeater {
            model: [
                {
                    label: "C",
                    kind: "clear",
                    variant: "tonal"
                },
                {
                    label: "( )",
                    kind: "paren",
                    variant: "tonal"
                },
                {
                    label: "%",
                    kind: "text",
                    text: "%",
                    variant: "tonal"
                },
                {
                    label: "÷",
                    kind: "text",
                    text: "÷",
                    variant: "tonal"
                },
                {
                    label: "7",
                    kind: "text",
                    text: "7",
                    variant: "neutral"
                },
                {
                    label: "8",
                    kind: "text",
                    text: "8",
                    variant: "neutral"
                },
                {
                    label: "9",
                    kind: "text",
                    text: "9",
                    variant: "neutral"
                },
                {
                    label: "×",
                    kind: "text",
                    text: "×",
                    variant: "tonal"
                },
                {
                    label: "4",
                    kind: "text",
                    text: "4",
                    variant: "neutral"
                },
                {
                    label: "5",
                    kind: "text",
                    text: "5",
                    variant: "neutral"
                },
                {
                    label: "6",
                    kind: "text",
                    text: "6",
                    variant: "neutral"
                },
                {
                    label: "−",
                    kind: "text",
                    text: "-",
                    variant: "tonal"
                },
                {
                    label: "1",
                    kind: "text",
                    text: "1",
                    variant: "neutral"
                },
                {
                    label: "2",
                    kind: "text",
                    text: "2",
                    variant: "neutral"
                },
                {
                    label: "3",
                    kind: "text",
                    text: "3",
                    variant: "neutral"
                },
                {
                    label: "+",
                    kind: "text",
                    text: "+",
                    variant: "tonal"
                },
                {
                    label: "0",
                    kind: "text",
                    text: "0",
                    variant: "neutral"
                },
                {
                    label: ".",
                    kind: "text",
                    text: ".",
                    variant: "neutral"
                },
                {
                    label: "⌫",
                    kind: "back",
                    variant: "neutral"
                },
                {
                    label: "=",
                    kind: "equals",
                    variant: "filled"
                }
            ]
            delegate: PillButton {
                required property var modelData
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                implicitHeight: 52
                variant: modelData.variant
                text: modelData.label
                Accessible.name: modelData.kind === "back" ? "Backspace" : modelData.kind === "clear" ? "Clear" : modelData.kind === "equals" ? "Equals" : modelData.label
                onClicked: {
                    if (modelData.kind === "clear")
                        root.clearAll();
                    else if (modelData.kind === "back")
                        root.backspace();
                    else if (modelData.kind === "equals")
                        root.equals();
                    else if (modelData.kind === "paren") {
                        const before = field.text.slice(0, field.cursorPosition);
                        const open = (before.match(/\(/g) || []).length - (before.match(/\)/g) || []).length;
                        root.put(open > 0 && /[0-9.)a-z!%]$/.test(before) ? ")" : "(");
                    } else
                        root.put(modelData.text);
                }
            }
        }
    }
    Item {
        Layout.fillHeight: true
    }
}
