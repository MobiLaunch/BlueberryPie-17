import QtQuick

QtObject {
    id: root
    property var model: []
    property Component delegate
    property var instances: []
    property bool ready: false
    function rebuild() {
        instances.forEach(item => item.destroy());
        const made = [];
        if (delegate)
            for (const entry of model || [])
                made.push(delegate.createObject(root, {
                    "modelData": entry
                }));
        instances = made;
    }
    onModelChanged: if (ready)
        rebuild()
    onDelegateChanged: if (ready)
        rebuild()
    Component.onCompleted: {
        ready = true;
        rebuild();
    }
}
