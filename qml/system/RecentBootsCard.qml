import QtQuick
import ".."

// Total time of the last startups (monitor.recentBoots, oldest first): one
// point per boot, from the left axis to the right edge, the newest hollow with
// its time always above it. Hovering snaps a line to the nearest boot and
// shows its time below it. A boot that
// never finished has no journal entry, so it is just not on the line.
Card {
    id: root

    readonly property var boots: monitor.recentBoots
    readonly property real scaleMax: niceTop(boots.reduce((top, v) => Math.max(top, v), 0))
    readonly property int newest: boots.length - 1
    // Boot under the mouse, or -1.
    property int hovered: -1

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

        // Y axis: top, middle and bottom of the scale.
        Repeater {
            model: 3

            Label {
                required property int index

                readonly property real value: root.scaleMax * (1 - index / 2)

                width: Config.bootsAxisWidth
                // Centred on its grid line, kept inside the card.
                y: Math.max(0, Math.min(plot.height - height,
                                        Math.round(plot.yAt(value) - height / 2)))
                text: Math.round(value) + " s"
                color: Config.fgDim
                font.pixelSize: Config.fontSizeSmall
            }
        }

        // X axis: boot number under each point, 1 = oldest.
        Repeater {
            model: root.boots.length

            Label {
                required property int index

                x: Math.round(plot.x + plot.xAt(index) - width / 2)
                y: chart.height - height
                text: index + 1
                color: Config.fgDim
                font.pixelSize: Config.fontSizeSmall
            }
        }

        Canvas {
            id: plot

            // Room for a dot on the edges; the grid box is exactly the
            // points' span, so the first boot sits on the axis.
            readonly property real inset: Config.bootsLastDotRadius + 1
            readonly property real leftX: Math.round(inset) + 0.5
            readonly property real rightX: Math.round(width - inset) + 0.5
            readonly property real topY: yAt(root.scaleMax)
            readonly property real bottomY: yAt(0)

            anchors.left: parent.left
            anchors.leftMargin: Config.bootsAxisWidth + Config.gap
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Config.bootsXAxisHeight

            onWidthChanged: requestPaint()
            onHeightChanged: requestPaint()

            // Points spread over the whole width; a lone boot sits on the right.
            function xAt(i) {
                const count = root.boots.length;
                if (count < 2)
                    return rightX;
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

                const boots = root.boots;

                // Dashed grid: a vertical line under each boot, horizontal
                // ones at the top and middle labels.
                ctx.strokeStyle = String(Config.gridLine);
                ctx.setLineDash(Config.bootsGridDash);
                ctx.beginPath();
                for (let i = 0; i < boots.length; i++) {
                    ctx.moveTo(xAt(i), topY);
                    ctx.lineTo(xAt(i), bottomY);
                }
                for (let k = 0; k < 2; k++) {
                    const y = yAt(root.scaleMax * (1 - k / 2));
                    ctx.moveTo(leftX, y);
                    ctx.lineTo(rightX, y);
                }
                ctx.stroke();

                // Solid axes: left and bottom.
                ctx.setLineDash([]);
                ctx.beginPath();
                ctx.moveTo(leftX, topY);
                ctx.lineTo(leftX, bottomY);
                ctx.lineTo(rightX, bottomY);
                ctx.stroke();

                if (boots.length === 0)
                    return;

                // Hover line, under the data so the line and dots stay on top.
                if (root.hovered >= 0) {
                    ctx.strokeStyle = String(Config.fgDim);
                    ctx.beginPath();
                    ctx.moveTo(xAt(root.hovered), topY);
                    ctx.lineTo(xAt(root.hovered), bottomY);
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

                const labelled = i => i === root.newest || i === root.hovered;

                ctx.fillStyle = String(Config.graphLine);
                for (let i = 0; i < boots.length; i++) {
                    if (labelled(i))
                        continue;
                    ctx.beginPath();
                    ctx.arc(xAt(i), yAt(boots[i]), Config.bootsDotRadius, 0, 2 * Math.PI);
                    ctx.fill();
                }

                // Labelled boots: hollow, black inside so the line stops at the rim.
                ctx.fillStyle = String(Config.menuBg);
                ctx.strokeStyle = String(Config.fgActive);
                ctx.lineWidth = Config.bootsLastDotStroke;
                for (let i = 0; i < boots.length; i++) {
                    if (!labelled(i))
                        continue;
                    ctx.beginPath();
                    ctx.arc(xAt(i), yAt(boots[i]), Config.bootsLastDotRadius, 0, 2 * Math.PI);
                    ctx.fill();
                    ctx.stroke();
                }
            }
        }

        // Newest time above its point, the hovered one below its own, so the
        // two stay apart; each flips side when it would leave the plot.
        ValueTag {
            index: root.newest
            above: true
        }

        ValueTag {
            index: root.hovered
            above: false
            visible: index >= 0 && index !== root.newest
        }

        MouseArea {
            x: plot.x
            width: plot.width
            height: plot.height
            hoverEnabled: true

            onPositionChanged: (mouse) => root.hovered = plot.nearest(mouse.x)
            onExited: root.hovered = -1
        }
    }

    // Black behind the text: over the plot it would cross the line.
    component ValueTag: Rectangle {
        property int index: -1
        property bool above: true

        readonly property real dotY: plot.y + plot.yAt(root.boots[index] ?? 0)
        readonly property real offset: Config.bootsLastDotRadius + Config.gap
        readonly property real upY: dotY - offset - height
        readonly property real downY: dotY + offset
        readonly property bool fitsUp: upY >= plot.y
        readonly property bool fitsDown: downY + height <= plot.y + plot.height

        // Centred on its point, kept inside the plot.
        x: Math.round(Math.max(plot.x, Math.min(plot.x + plot.width - width,
                                                plot.x + plot.xAt(index) - width / 2)))
        y: Math.round((above ? fitsUp || !fitsDown : !fitsDown && fitsUp) ? upY : downY)
        width: tagText.implicitWidth + 2 * Config.bootsValuePad
        height: tagText.implicitHeight
        color: Config.menuBg

        Label {
            id: tagText

            x: Config.bootsValuePad
            text: Format.seconds(root.boots[parent.index] ?? -1)
            color: Config.fgActive
        }
    }
}
