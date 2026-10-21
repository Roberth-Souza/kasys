import QtQuick
import ".."

// A card with one big value and a dim line under it.
Card {
    id: root

    property string value: Format.missing
    property string detail: ""

    Column {
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Config.statGap

        Label {
            width: parent.width
            height: Config.bigValueHeight
            verticalAlignment: Text.AlignVCenter
            text: root.value
            color: root.value === Format.missing ? Config.fgDim : Config.fgActive
            font.pixelSize: Config.fontSizeHuge
        }

        Label {
            width: parent.width
            height: Config.statDetailHeight
            text: root.detail
            color: Config.fgDim
        }
    }
}
