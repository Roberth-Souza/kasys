import QtQuick
import "."

// The root filesystem only: on btrfs every subvolume shares its numbers.
Card {
    title: "Disk"
    glyph: Config.glyphDisk

    headerRight: Row {
        spacing: Config.blockGap

        UsedOfTotal {
            used: monitor.diskUsed
            total: monitor.diskTotal
        }

        Label {
            text: Format.percent(monitor.diskPercent)
            color: Config.fgActive
        }
    }

    Column {
        anchors.fill: parent
        spacing: Config.sectionGap

        Graph {
            width: parent.width
            height: Config.graphHeight
            values: monitor.diskHistory
        }

        MeterRow {
            width: parent.width
            label: "/"
            value: Format.bytes(monitor.diskUsed)
            fraction: monitor.diskPercent / 100
        }
    }
}
