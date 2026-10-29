import QtQuick
import ".."
import "art.js" as Art

// One disk at a time, picked in the heading; opens on the disk holding /.
// Model, size, kind and filesystem beside the drive, then the space of its
// largest mounted partition (hidden when nothing is mounted); SMART on the
// right, wear fields on NVMe only.
PartRow {
    id: root

    // What the user picked; "" or a vanished disk falls back to the one
    // holding /, then to the first.
    property string picked: ""
    readonly property var shown: monitor.storageDisks.find(d => d.name === root.picked)
                                 ?? monitor.storageDisks.find(d => d.name === monitor.rootDisk)
                                 ?? monitor.storageDisks[0] ?? null
    readonly property string kind: shown ? shown.kind : ""
    readonly property bool nvme: kind === "NVMe"
    readonly property bool mounted: root.shown !== null && root.shown.percent >= 0

    readonly property var detail: root.shown
        ? [Format.bytes(root.shown.size), Format.text(root.kind), Format.text(root.shown.fstype)]
            .filter(part => part !== Format.missing)
        : []

    readonly property var poweredOn: ({
        "key": "Powered on",
        "value": Format.hours(root.shown ? root.shown.powerOnHours : -1)
    })

    // An unknown kind gets the plain SSD: a spinning platter would claim too much.
    art: kind === "NVMe" ? Art.nvme() : kind === "HDD" ? Art.hdd() : Art.ssd()
    artWidth: kind === "NVMe" ? Config.artNvmeWidth
            : kind === "HDD" ? Config.artHddWidth : Config.artSsdWidth

    PartTitle {
        width: parent.width
        title: "Storage"
        picker: Dropdown {
            options: monitor.storageDisks.map(d => d.name)
            current: root.shown ? root.shown.name : ""
            onPicked: option => root.picked = option
        }
        name: Format.text(root.shown ? root.shown.model : "")
        detail: root.detail.join(" · ")
    }

    Item {
        visible: root.mounted
        width: parent.width
        height: Config.partBarHeight + 2 * Config.partBarGap

        Bar {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width
            height: Config.partBarHeight
            fraction: root.mounted ? root.shown.percent / 100 : -1
        }
    }

    Item {
        visible: root.mounted
        width: parent.width
        height: Config.partKeyHeight

        Row {
            Label {
                text: Format.bytes(root.mounted ? root.shown.used : -1)
                color: Config.fgActive
            }

            Label {
                text: " used · " + Format.percent(root.mounted ? root.shown.percent : -1)
            }
        }

        Label {
            anchors.right: parent.right
            text: Format.bytes(root.mounted ? root.shown.available : -1) + " available"
        }
    }

    live: [
        StatRow {
            width: parent.width
            valueSize: Config.fontSizeLarge
            valueHeight: Config.partMidHeight
            stats: [
                { "key": "Temperature", "value": Format.celsius(root.shown ? root.shown.temp : -1) },
                { "key": "Health", "value": Format.text(root.shown ? root.shown.health : "") }
            ]
        },
        PartRule {
            width: parent.width
        },
        StatRow {
            width: parent.width
            // Wear needs NVMe's own fields: ATA has no standard one.
            stats: root.nvme ? [
                { "key": "Lifespan used", "value": Format.percent(root.shown.lifespanUsed) },
                { "key": "Total written", "value": Format.bytes(root.shown.written) },
                root.poweredOn
            ] : [root.poweredOn]
        }
    ]
}
