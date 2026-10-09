import QtQuick
import "."

// A scrolling line graph: the newest sample on the right edge, `capacity`
// samples across. The first series is filled, the optional second one is a
// dimmer line on top. `maxValue` > 0 fixes the scale (percentages); 0 picks a
// round scale from the data (rates). An empty series draws only the grid.
Item {
    id: root

    property var values: []
    property var secondValues: []
    property real maxValue: 100
    property int capacity: Config.historyLength
    property int labelWidth: Config.percentLabelWidth
    property var formatLabel: (v) => Math.round(v) + "%"

    readonly property real scaleMax: root.maxValue > 0
                                     ? root.maxValue
                                     : Format.niceMax(Math.max(root.peak(root.values),
                                                               root.peak(root.secondValues)))

    function peak(list) {
        let top = 0;
        for (let i = 0; i < list.length; i++)
            top = Math.max(top, list[i]);
        return top;
    }

    onValuesChanged: plot.requestPaint()
    onSecondValuesChanged: plot.requestPaint()

    // The axis: top, middle and bottom of the scale.
    Repeater {
        model: 3

        Label {
            required property int index

            width: root.labelWidth
            y: Math.round(index * (root.height - height) / 2)
            text: root.formatLabel(root.scaleMax * (1 - index / 2))
            color: Config.fgDim
            font.pixelSize: Config.fontSizeSmall
        }
    }

    Canvas {
        id: plot

        anchors.left: parent.left
        anchors.leftMargin: root.labelWidth + Config.gap
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()

        function xAt(i, count) {
            const step = width / (root.capacity - 1);
            return width - (count - 1 - i) * step;
        }

        function yAt(v) {
            const f = Math.max(0, Math.min(1, v / root.scaleMax));
            // Inset by a pixel so a flat zero line stays visible.
            return Math.round(1 + (height - 2) * (1 - f)) + 0.5;
        }

        function tracePath(ctx, list) {
            ctx.beginPath();
            for (let i = 0; i < list.length; i++) {
                const x = xAt(i, list.length);
                const y = yAt(list[i]);
                if (i === 0)
                    ctx.moveTo(x, y);
                else
                    ctx.lineTo(x, y);
            }
        }

        onPaint: {
            const ctx = getContext("2d");
            ctx.reset();
            ctx.lineWidth = 1;

            // Faint vertical grid every 10 samples, from the right edge.
            ctx.strokeStyle = String(Config.gridLineFaint);
            ctx.beginPath();
            for (let i = root.capacity - 1; i >= 0; i -= 10) {
                const x = Math.round(xAt(i, root.capacity)) - 0.5;
                ctx.moveTo(x, 0);
                ctx.lineTo(x, height);
            }
            ctx.stroke();

            // Horizontal grid at the three axis labels.
            ctx.strokeStyle = String(Config.gridLine);
            ctx.beginPath();
            for (let k = 0; k <= 2; k++) {
                const y = Math.round(k * (height - 1) / 2) + 0.5;
                ctx.moveTo(0, y);
                ctx.lineTo(width, y);
            }
            ctx.stroke();

            const first = root.values;
            if (first.length > 1) {
                tracePath(ctx, first);
                ctx.lineTo(xAt(first.length - 1, first.length), height);
                ctx.lineTo(xAt(0, first.length), height);
                ctx.closePath();
                ctx.fillStyle = String(Config.graphFill);
                ctx.fill();

                tracePath(ctx, first);
                ctx.strokeStyle = String(Config.graphLine);
                ctx.stroke();
            }

            const second = root.secondValues;
            if (second.length > 1) {
                tracePath(ctx, second);
                ctx.strokeStyle = String(Config.graphLineSecond);
                ctx.stroke();
            }
        }
    }
}
