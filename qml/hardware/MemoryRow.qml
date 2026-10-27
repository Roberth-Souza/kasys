import QtQuick
import ".."
import "art.js" as Art

// Installed size and type, speed and channels beside the stick, the slots on
// the right. Slots are drawn for boards of 2 or 4; other counts get a
// "N of M slots populated" line instead.
PartRow {
    id: root

    readonly property var slots: monitor.memorySlots
    readonly property int populated: slots.filter(slot => slot.populated).length
    readonly property bool drawn: slots.length === 2 || slots.length === 4
    readonly property var detail: [Format.mts(monitor.memorySpeed), Format.channels(monitor.memoryChannels)]
        .filter(part => part !== Format.missing)

    art: Art.ram()
    artWidth: Config.artRamWidth

    PartTitle {
        width: parent.width
        title: "Memory"
        name: monitor.memoryInstalled < 0 ? Format.missing
            : Format.bytes(monitor.memoryInstalled) + (monitor.memoryType === "" ? "" : " " + monitor.memoryType)
        detail: root.detail.length ? root.detail.join(" · ") : Format.missing
    }

    live: [
        Row {
            id: slotRow

            visible: root.drawn
            width: parent.width
            spacing: Config.partSlotGap

            Repeater {
                model: root.drawn ? root.slots : []

                Column {
                    required property var modelData

                    width: (slotRow.width - (root.slots.length - 1) * slotRow.spacing) / root.slots.length

                    LineArt {
                        width: parent.width
                        art: Art.slot(modelData.populated)
                        color: modelData.populated ? Config.artLine : Config.fgDim
                    }

                    Label {
                        width: parent.width
                        height: Config.partKeyHeight
                        verticalAlignment: Text.AlignVCenter
                        horizontalAlignment: Text.AlignHCenter
                        text: modelData.populated ? Format.bytes(modelData.size) : "empty"
                        color: modelData.populated ? Config.fgActive : Config.fgDim
                        font.pixelSize: Config.fontSizeSmall
                    }
                }
            }
        },
        // Only when the slots are not drawn: the drawing already says it.
        Label {
            visible: !root.drawn
            width: parent.width
            height: Config.partKeyHeight
            verticalAlignment: Text.AlignVCenter
            text: root.slots.length ? root.populated + " of " + root.slots.length + " slots populated" : Format.missing
            color: root.slots.length ? Config.fg : Config.fgDim
        }
    ]
}
