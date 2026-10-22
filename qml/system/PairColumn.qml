import QtQuick
import ".."

// Label / value lines with the values lined up in one column. `rows` is a
// list of { "label": ..., "value": ... }; a missing value is drawn dim.
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
                width: Config.pairLabelWidth - Config.gap
                anchors.verticalCenter: parent.verticalCenter
                text: modelData.label
            }

            Label {
                x: Config.pairLabelWidth
                width: parent.width - x
                anchors.verticalCenter: parent.verticalCenter
                text: modelData.value
                color: modelData.value === Format.missing ? Config.fgDim : Config.fgActive
            }
        }
    }
}
