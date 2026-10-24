import QtQuick
import ".."

// A small dim label over its value. A value not built yet is drawn small
// whatever `valueSize`, so it fits the cell.
Column {
    id: root

    property string key: ""
    property string value: Format.missing
    property int valueSize: Config.fontSizeMedium
    property int valueHeight: Config.partValueHeight

    readonly property bool notBuilt: value === Format.notBuilt
    // Unelided width: what the cell would take if it had the room.
    readonly property real naturalWidth: Math.max(keyLabel.implicitWidth, valueLabel.implicitWidth)

    Label {
        id: keyLabel

        width: root.width
        height: Config.partKeyHeight
        verticalAlignment: Text.AlignVCenter
        text: root.key
        color: Config.fgDim
        font.pixelSize: Config.fontSizeSmall
    }

    Label {
        id: valueLabel

        width: root.width
        height: root.valueHeight
        verticalAlignment: Text.AlignVCenter
        text: root.value
        color: Format.absent(root.value) ? Config.fgDim : Config.fgActive
        font.pixelSize: root.notBuilt ? Config.fontSize : root.valueSize
    }
}
