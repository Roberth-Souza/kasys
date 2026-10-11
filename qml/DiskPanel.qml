import QtQuick
import "."

// Only disks with something mounted. Heading: a disk picker, then the space
// used on the picked disk's largest mounted partition. Graph: its active time,
// the share of each second it had a request in flight. Rows: free space on
// every disk, the bar filled like `df` Use%, the picked one bright.
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
            used: root.shown ? root.shown.used : -1
            total: root.shown ? root.shown.total : -1
        }

        Label {
            text: Format.percent(root.shown ? root.shown.percent : -1)
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
                    value: Format.bytes(modelData.available)
                    fraction: modelData.percent / 100
                }
            }

            // No disk could be read: one empty row instead of a bare card.
            MeterRow {
                visible: monitor.disks.length === 0
                width: parent.width
                label: "Free"
            }
        }
    }
}
