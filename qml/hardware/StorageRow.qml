import QtQuick
import ".."
import "art.js" as Art

// The disk holding /: model, size and usage beside the drive, SMART on the
// right.
PartRow {
    id: root

    readonly property var detail: [Format.bytes(monitor.diskSize), Format.text(monitor.diskKind)]
        .filter(part => part !== Format.missing)

    art: Art.nvme()
    artWidth: Config.artNvmeWidth

    PartTitle {
        width: parent.width
        title: "Storage"
        name: Format.text(monitor.diskModel)
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
                { "key": "Temperature", "value": Format.celsius(monitor.diskTemp) },
                { "key": "Health", "value": Format.text(monitor.diskHealth) }
            ]
        },
        PartRule {
            width: parent.width
        },
        StatRow {
            width: parent.width
            stats: [
                { "key": "Lifespan used", "value": Format.percent(monitor.diskLifespanUsed) },
                { "key": "Total written", "value": Format.bytes(monitor.diskWritten) },
                { "key": "Powered on", "value": Format.hours(monitor.diskPowerOnHours) }
            ]
        }
    ]
}
