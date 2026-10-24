import QtQuick
import ".."

// Dim label / value lines. `rows` is a list of { label, value, pending }.
Column {
    id: root

    property var rows: []

    Repeater {
        model: root.rows

        Item {
            required property var modelData

            width: root.width
            height: Config.pairRowHeight

            Label {
                width: Config.partPairLabelWidth - Config.gap
                height: parent.height
                verticalAlignment: Text.AlignVCenter
                text: modelData.label
                color: Config.fgDim
                font.pixelSize: Config.fontSizeSmall
            }

            PendingText {
                x: Config.partPairLabelWidth
                width: parent.width - x
                height: parent.height
                text: modelData.value
                pending: modelData.pending === true
            }
        }
    }
}
