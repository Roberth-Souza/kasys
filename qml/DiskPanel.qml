import QtQuick
import "."

// Heading: a disk picker, then space used on the root filesystem (on btrfs
// every subvolume shares its numbers). Body: active time, the share of each
// second a disk had a request in flight. The graph follows the picked disk;
// the rows list every disk, the picked one bright.
Card {
    id: root

    // What the user picked; "" or an unplugged disk falls back to the first.
    property string picked: ""
    readonly property var shown: monitor.disks.find((d) => d.name === root.picked)
                                 ?? monitor.disks[0] ?? null

    title: "Disk"
    glyph: Config.glyphDisk

    headerLeft: Dropdown {
        options: monitor.disks.map((d) => d.name)
        current: root.shown ? root.shown.name : ""
        onPicked: (option) => root.picked = option
    }

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
            values: root.shown ? root.shown.history : []
        }

        Column {
            width: parent.width

            Repeater {
                model: monitor.disks

                MeterRow {
                    required property var modelData

                    width: parent.width
                    label: modelData.name
                    labelColor: root.shown && modelData.name === root.shown.name
                                ? Config.fgActive : Config.fg
                    value: Format.percent(modelData.percent)
                    fraction: modelData.percent / 100
                }
            }

            // No disk could be read: one empty row instead of a bare card.
            MeterRow {
                visible: monitor.disks.length === 0
                width: parent.width
                label: "Active"
            }
        }
    }
}
