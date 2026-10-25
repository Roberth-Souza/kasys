import QtQuick
import "."

// Download (filled, bright) and upload (dim line) on one graph that takes the
// whole card. The bridge keeps the scale steady; short bursts are clipped.
Card {
    title: "Network"
    glyph: Config.glyphNetwork

    headerRight: Row {
        spacing: Config.blockGap

        Label {
            text: Config.glyphDown + " " + Format.rate(monitor.netDown)
            color: Config.graphLine
        }

        Label {
            text: Config.glyphUp + " " + Format.rate(monitor.netUp)
            color: Config.graphLineSecond
        }
    }

    Graph {
        anchors.fill: parent
        values: monitor.netDownHistory
        secondValues: monitor.netUpHistory
        maxValue: Format.niceMax(monitor.netScale)
        labelWidth: Config.rateLabelWidth
        formatLabel: (v) => Format.rate(v)
    }
}
