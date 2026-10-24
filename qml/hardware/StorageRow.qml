import QtQuick
import ".."
import "art.js" as Art

// The disk holding /: model, size and usage beside the drive, SMART on the
// right.
PartRow {
    art: Art.nvme()
    artWidth: Config.artNvmeWidth

    PartTitle {
        width: parent.width
        title: "Storage"
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
                { "key": "Temperature", "value": Format.notBuilt },
                { "key": "Health", "value": Format.notBuilt }
            ]
        },
        PartRule {
            width: parent.width
        },
        StatRow {
            width: parent.width
            stats: [
                { "key": "Lifespan used", "value": Format.notBuilt },
                { "key": "Total written", "value": Format.notBuilt },
                { "key": "Powered on", "value": Format.notBuilt }
            ]
        }
    ]
}
