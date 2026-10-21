import QtQuick
import ".."

// One line of a key/value card: label on the left, value on the right.
// `pending` rows have no collector yet and say so in place of the value.
Item {
    id: root

    property string label: ""
    property string value: Format.missing
    property bool pending: false

    height: Config.infoRowHeight

    Label {
        id: key

        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        elide: Text.ElideNone
        text: root.label
    }

    Label {
        anchors.left: key.right
        anchors.leftMargin: Config.gap
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        horizontalAlignment: Text.AlignRight
        text: root.pending ? Format.notBuilt : root.value
        color: root.pending || root.value === Format.missing ? Config.fgDim : Config.fgActive
    }
}
