import QtQuick
import ".."

// One drawing from art.js, scaled to `width` (height follows its aspect).
// Strokes are divided by the scale, so every drawing has the same line
// weight whatever size it is drawn at.
Canvas {
    id: root

    // { w, h, shapes } from art.js.
    property var art: null
    property color color: Config.artLine

    height: art ? width * art.h / art.w : 0

    onArtChanged: requestPaint()
    onColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()

    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        if (!root.art || root.width <= 0)
            return;
        const k = root.width / root.art.w;
        ctx.scale(k, k);
        ctx.strokeStyle = root.color;
        ctx.fillStyle = root.color;
        ctx.lineJoin = "round";
        ctx.textAlign = "center";
        for (const s of root.art.shapes) {
            ctx.globalAlpha = s.thin ? Config.artThinOpacity : 1;
            ctx.lineWidth = (s.thin ? Config.artThinStroke : Config.artStroke) / k;
            ctx.beginPath();
            switch (s.kind) {
            case "path":
                ctx.path = s.d;
                break;
            case "rect":
                if (s.r > 0)
                    ctx.roundedRect(s.x, s.y, s.w, s.h, s.r, s.r);
                else
                    ctx.rect(s.x, s.y, s.w, s.h);
                break;
            case "circle":
                ctx.arc(s.cx, s.cy, s.r, 0, 2 * Math.PI);
                break;
            case "text":
                ctx.font = s.size + "px \"" + Config.font + "\"";
                const fit = s.maxWidth / ctx.measureText(s.text).width;
                if (fit < 1)
                    ctx.font = (s.size * fit) + "px \"" + Config.font + "\"";
                ctx.fillText(s.text, s.x, s.y);
                continue;
            }
            ctx.stroke();
        }
    }
}
