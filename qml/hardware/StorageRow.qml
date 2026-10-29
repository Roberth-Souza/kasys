import QtQuick
import ".."
import "art.js" as Art

// One disk at a time, picked in the heading; opens on the disk holding /.
// Model, size and kind beside the drive, SMART on the right.
PartRow {
    id: root

    // What the user picked; "" or a vanished disk falls back to the one
    // holding /, then to the first.
    property string picked: ""
    readonly property var shown: monitor.storageDisks.find(d => d.name === root.picked)
                                 ?? monitor.storageDisks.find(d => d.name === monitor.rootDisk)
                                 ?? monitor.storageDisks[0] ?? null
    readonly property string kind: shown ? shown.kind : ""
    // SMART is NVMe only for now; HDDs never have the wear fields.
    readonly property bool nvme: kind === "NVMe"
    readonly property bool hasWear: kind !== "HDD"

    readonly property var detail: root.shown
        ? [Format.bytes(root.shown.size), Format.text(root.kind)].filter(part => part !== Format.missing)
        : []

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
        // PCIe link and filesystem have no collector yet.
        detail: root.detail.join(" · ")
        detailPending: true
    }

    Item {
        width: parent.width
        height: Config.partBarHeight + 2 * Config.partBarGap

        Bar {
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width
            height: Config.partBarHeight
        }
    }

    live: [
        StatRow {
            width: parent.width
            valueSize: Config.fontSizeLarge
            valueHeight: Config.partMidHeight
            stats: [
                { "key": "Temperature", "value": Format.celsius(root.shown ? root.shown.temp : -1) },
                {
                    "key": "Health",
                    "value": !root.shown ? Format.missing
                           : root.nvme ? Format.text(root.shown.health) : Format.notBuilt
                }
            ]
        },
        PartRule {
            width: parent.width
        },
        StatRow {
            width: parent.width
            stats: [
                {
                    "key": "Lifespan used",
                    "value": root.nvme ? Format.percent(root.shown.lifespanUsed)
                           : root.hasWear && root.shown ? Format.notBuilt : Format.missing
                },
                {
                    "key": "Total written",
                    "value": root.nvme ? Format.bytes(root.shown.written)
                           : root.hasWear && root.shown ? Format.notBuilt : Format.missing
                },
                {
                    "key": "Powered on",
                    "value": !root.shown ? Format.missing
                           : root.nvme ? Format.hours(root.shown.powerOnHours) : Format.notBuilt
                }
            ]
        }
    ]
}
