import QtQuick
import "."

Card {
    title: "Memory"
    glyph: Config.glyphMemory

    headerRight: Row {
        spacing: Config.blockGap

        UsedOfTotal {
            used: monitor.memUsed
            total: monitor.memTotal
        }

        Label {
            text: Format.percent(monitor.memPercent)
            color: Config.fgActive
        }
    }

    Column {
        anchors.fill: parent
        spacing: Config.sectionGap

        Graph {
            width: parent.width
            height: Config.graphHeight
            values: monitor.memHistory
        }

        Column {
            width: parent.width

            MeterRow {
                width: parent.width
                label: "Used"
                value: Format.bytes(monitor.memUsed)
                fraction: monitor.memTotal > 0 ? monitor.memUsed / monitor.memTotal : -1
            }

            MeterRow {
                width: parent.width
                label: "Available"
                valueColor: Config.fg
                value: Format.bytes(monitor.memAvailable)
                fraction: monitor.memTotal > 0 ? monitor.memAvailable / monitor.memTotal : -1
            }
        }
    }
}
