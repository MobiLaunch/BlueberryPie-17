import QtQuick
import "."
import "../services"

// The default wallpaper, drawn from the current color roles so it follows the
// palette and light/dark preference (Material You style). Vector, any resolution.
Image {
    id: root
    function mix(a, b, amount) {
        return Qt.rgba(a.r + (b.r - a.r) * amount, a.g + (b.g - a.g) * amount, a.b + (b.b - a.b) * amount, 1);
    }
    readonly property string flower: {
        const points = [];
        for (let i = 0; i <= 240; i++) {
            const angle = i * Math.PI / 120;
            const radius = 255 + 30 * Math.cos(angle * 8);
            points.push((680 + Math.cos(angle) * radius).toFixed(1) + "," + (350 + Math.sin(angle) * radius).toFixed(1));
        }
        return points.join(" ");
    }
    readonly property string svg: {
        const base = Theme.primaryContainer;
        const waveA = Theme.hex(mix(base, Theme.primary, 0.26));
        const waveB = Theme.hex(Theme.tertiaryContainer);
        const sun = Theme.hex(mix(Theme.tertiaryContainer, Theme.surface, 0.25));
        const bloom = Theme.hex(mix(base, Theme.primary, 0.42));
        const stroke = Theme.hex(mix(Theme.tertiaryContainer, Theme.tertiary, 0.35));
        const dot = Theme.hex(mix(Theme.secondaryContainer, Theme.tertiary, 0.2));
        const hole = Theme.hex(base);
        return "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1920 1080'>" + "<rect width='1920' height='1080' fill='" + Theme.hex(base) + "'/>" + "<path d='M0 670Q400 450 760 810T1600 770V1080H0Z' fill='" + waveA + "'/>" + "<path d='M800 1080Q760 520 1200 500T1920 190V1080Z' fill='" + waveB + "'/>" + "<ellipse cx='1580' cy='180' rx='330' ry='310' fill='" + sun + "'/>" + "<ellipse cx='1580' cy='180' rx='190' ry='180' fill='" + hole + "'/>" + "<polygon points='" + flower + "' fill='" + bloom + "' transform='translate(270 70) rotate(-12 680 350)'/>" + "<circle cx='950' cy='420' r='140' fill='" + hole + "'/>" + "<path d='M1550 820q75-170 175-115t140 180' fill='none' stroke='" + stroke + "' stroke-width='60' stroke-linecap='round'/>" + "<circle cx='410' cy='950' r='82' fill='" + dot + "'/>" + "</svg>";
    }
    source: "data:image/svg+xml;utf8," + encodeURIComponent(svg)
    sourceSize: Qt.size(1920, 1080)
    fillMode: Image.PreserveAspectCrop
    smooth: true
}
