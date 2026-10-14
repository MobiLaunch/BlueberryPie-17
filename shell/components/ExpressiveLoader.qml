import QtQuick
import "../services"

Item {
    id: root
    implicitWidth: 48
    implicitHeight: 48
    property real phase: 0
    property color color: Theme.primaryStrong
    Canvas {
        id: canvas
        anchors.fill: parent
        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            ctx.fillStyle = root.color;
            ctx.beginPath();
            const cx = width / 2, cy = height / 2, radius = Math.min(width, height) * .35;
            for (let i = 0; i <= 120; i++) {
                const a = i / 120 * Math.PI * 2;
                const r = radius * (1 + .16 * Math.sin(a * 6 + root.phase * Math.PI * 2));
                if (i === 0)
                    ctx.moveTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
                else
                    ctx.lineTo(cx + Math.cos(a) * r, cy + Math.sin(a) * r);
            }
            ctx.closePath();
            ctx.fill();
        }
    }
    onPhaseChanged: canvas.requestPaint()
    onColorChanged: canvas.requestPaint()
    NumberAnimation on phase {
        from: 0
        to: 1
        duration: 1400
        loops: Animation.Infinite
        running: root.visible && !Theme.reducedMotion
    }
    NumberAnimation on rotation {
        from: 0
        to: 360
        duration: 2200
        loops: Animation.Infinite
        running: root.visible && !Theme.reducedMotion
    }
}
