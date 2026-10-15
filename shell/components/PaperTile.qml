import QtQuick
import QtQuick.Controls
import "."
import "../services"

// A wallpaper choice: picture preview (or the live themed art) with a name.
Button {
    id: root
    property string title: ""
    property string preview: ""
    property bool current: false
    signal picked
    implicitWidth: 148
    implicitHeight: 128
    leftPadding: 0
    rightPadding: 0
    topPadding: 0
    bottomPadding: 0
    hoverEnabled: true
    focusPolicy: Qt.StrongFocus
    Accessible.name: title + " wallpaper" + (current ? ", selected" : "")
    Accessible.checkable: true
    Accessible.checked: current
    onClicked: picked()
    background: Item {}
    contentItem: Column {
        spacing: 6
        Rectangle {
            width: root.width
            height: 96
            radius: root.current ? 28 : 18
            color: Theme.surfaceContainerHigh
            clip: true
            border.width: root.current || root.visualFocus ? 3 : 0
            border.color: Theme.primary
            Behavior on radius {
                NumberAnimation {
                    duration: Theme.standard
                    easing.type: Easing.OutBack
                }
            }
            WallpaperArt {
                anchors.fill: parent
                visible: root.preview.length === 0
            }
            Image {
                anchors.fill: parent
                source: root.preview
                visible: root.preview.length > 0 && status === Image.Ready
                fillMode: Image.PreserveAspectCrop
                asynchronous: true
            }
            Rectangle {
                visible: root.current
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.margins: 8
                width: 24
                height: 24
                radius: 12
                color: Theme.primary
                Symbol {
                    anchors.centerIn: parent
                    width: 18
                    height: 18
                    name: "check"
                    color: Theme.primaryInk
                }
            }
        }
        Label {
            width: root.width
            text: root.title
            role: "labelMedium"
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
    }
}
