import QtQuick
import ".."
import "art.js" as Art

// Total, type and speed beside the stick, the slots on the right. Until the
// memory collector exists the slots are drawn dim and empty.
PartRow {
    art: Art.ram()
    artWidth: Config.artRamWidth

    PartTitle {
        width: parent.width
        title: "Memory"
    }

    live: [
        Row {
            id: slots

            width: parent.width
            spacing: Config.partSlotGap

            Repeater {
                model: Config.memorySlots

                LineArt {
                    width: (slots.width - (Config.memorySlots - 1) * slots.spacing) / Config.memorySlots
                    art: Art.slot(false)
                    color: Config.fgDim
                }
            }
        },
        Item {
            width: parent.width
            height: Config.partRuleGap
        },
        PendingText {
            width: parent.width
            height: Config.partKeyHeight
            pending: true
        }
    ]
}
