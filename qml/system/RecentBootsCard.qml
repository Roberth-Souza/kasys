import QtQuick
import ".."

// Total time of the last startups (monitor.recentBoots, oldest first): one
// point per boot, the newest hollow with its time beside it. Hovering snaps a
// line to the nearest boot and shows that one instead. A boot that never
// finished has no journal entry, so it is just not on the line.
Card {
    id: root

    readonly property var boots: monitor.recentBoots
    readonly property real scaleMax: niceTop(boots.reduce((top, v) => Math.max(top, v), 0))
    // Boot under the mouse, or -1; the labelled point falls back to the newest.
    property int hovered: -1
    readonly property int focused: hovered >= 0 ? hovered : boots.length - 1

    // A round axis top in seconds, so the labels stay whole numbers.
    function niceTop(peak) {
        for (const step of Config.bootsScaleSteps) {
            if (step >= peak)
                return step;
        }
        return Math.ceil(peak / 60) * 60;
    }

    title: "Recent boots"
    glyph: Config.glyphRecentBoots

    headerRight: Label {
        height: Config.cardTitleHeight
        verticalAlignment: Text.AlignVCenter
        visible: root.boots.length > 0
        text: "Last " + root.boots.length + (root.boots.length === 1 ? " startup" : " startups")
        color: Config.fgDim
    }

    onBootsChanged: {
        hovered = -1;
        plot.requestPaint();
    }
    onHoveredChanged: plot.requestPaint()

    Label {
        visible: root.boots.length === 0
        anchors.centerIn: parent
        text: Format.missing
        color: Config.fgDim
    }

    Item {
        id: chart

        visible: root.boots.length > 0
        anchors.fill: parent

        // Axis: top, middle and bottom of the scale.
        Repeater {
            model: 3

            Label {
                required property int index

                width: Config.bootsAxisWidth
                y: Math.round(index * (chart.height - height) / 2)
                text: Math.round(root.scaleMax * (1 - index / 2)) + " s"
                color: Config.fgDim
                font.pixelSize: Config.fontSizeSmall
            }
        }

        Canvas {
            id: plot

            readonly property real inset: Config.bootsLastDotRadius + 1

            anchors.left: parent.left
            anchors.leftMargin: Config.bootsAxisWidth + Config.gap
            anchors.right: parent.right
            anchors.rightMargin: Config.bootsValueWidth
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()

            // Points spread over the whole width; a lone boot sits on the right.
            function xAt(i) {
                const count = root.boots.length;
                if (count < 2)
                    return width - inset;
                return Math.round(inset + i * (width - 2 * inset) / (count - 1)) + 0.5;
            }

            function yAt(v) {
                const f = Math.max(0, Math.min(1, v / root.scaleMax));
                return Math.round(inset + (height - 2 * inset) * (1 - f)) + 0.5;
            }

            // The boot whose x is nearest to `x` (plot coordinates).
            function nearest(x) {
                const count = root.boots.length;
                if (count < 2)
                    return count - 1;
                const step = (width - 2 * inset) / (count - 1);
                return Math.max(0, Math.min(count - 1, Math.round((x - inset) / step)));
            }

            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                ctx.lineWidth = 1;

                // Faint vertical line under each boot.
                ctx.strokeStyle = String(Config.gridLineFaint);
                ctx.beginPath();
                for (let i = 0; i < root.boots.length; i++) {
                    ctx.moveTo(xAt(i), 0);
                    ctx.lineTo(xAt(i), height);
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

                const boots = root.boots;
                if (boots.length === 0)
                    return;

                // Hover line, under the data so the line and dots stay on top.
                if (root.hovered >= 0) {
                    ctx.strokeStyle = String(Config.fgDim);
                    ctx.beginPath();
                    ctx.moveTo(xAt(root.hovered), 0);
                    ctx.lineTo(xAt(root.hovered), height);
                    ctx.stroke();
                }

                ctx.strokeStyle = String(Config.graphLine);
                ctx.beginPath();
                for (let i = 0; i < boots.length; i++) {
                    if (i === 0)
                        ctx.moveTo(xAt(i), yAt(boots[i]));
                    else
                        ctx.lineTo(xAt(i), yAt(boots[i]));
                }
                ctx.stroke();

                ctx.fillStyle = String(Config.graphLine);
                for (let i = 0; i < boots.length; i++) {
                    if (i === root.focused)
                        continue;
                    ctx.beginPath();
                    ctx.arc(xAt(i), yAt(boots[i]), Config.bootsDotRadius, 0, 2 * Math.PI);
                    ctx.fill();
                }

                // The labelled boot: hollow, black inside so the line stops at its rim.
                const f = root.focused;
                ctx.beginPath();
                ctx.arc(xAt(f), yAt(boots[f]), Config.bootsLastDotRadius, 0, 2 * Math.PI);
                ctx.fillStyle = String(Config.menuBg);
                ctx.fill();
                ctx.strokeStyle = String(Config.fgActive);
                ctx.lineWidth = Config.bootsLastDotStroke;
                ctx.stroke();
            }
        }

        // Black behind the text: over the plot it would cross the line.
        Rectangle {
            x: plot.x + plot.xAt(root.focused) + Config.bootsLastDotRadius + Config.gap
            y: Math.round(plot.y + plot.yAt(root.boots[root.focused] ?? 0) - height / 2)
            width: value.implicitWidth + 2 * Config.bootsValuePad
            height: value.implicitHeight
            color: Config.menuBg

            Label {
                id: value

                x: Config.bootsValuePad
                text: Format.seconds(root.boots[root.focused] ?? -1)
                color: Config.fgActive
            }
        }

        MouseArea {
            x: plot.x
            width: plot.width
            height: parent.height
            hoverEnabled: true

            onPositionChanged: (mouse) => root.hovered = plot.nearest(mouse.x)
            onExited: root.hovered = -1
        }
    }
}
