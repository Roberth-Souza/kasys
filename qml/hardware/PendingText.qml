import QtQuick
import ".."

// A line of text that may still miss a part with no collector yet: that part
// trails it, dim, as Format.notBuilt.
Row {
    id: root

    property string text: ""
    property bool pending: false
    property color color: Config.fg
    property int pixelSize: Config.fontSize

    Label {
        id: shown

        width: Math.min(implicitWidth, root.width - (rest.visible ? rest.implicitWidth : 0))
        height: root.height
        verticalAlignment: Text.AlignVCenter
        text: root.text
        color: Format.absent(root.text) ? Config.fgDim : root.color
        font.pixelSize: root.pixelSize
    }

    Label {
        id: rest

        visible: root.pending
        height: root.height
        verticalAlignment: Text.AlignVCenter
        text: (root.text === "" ? "" : " · ") + Format.notBuilt
        color: Config.fgDim
        font.pixelSize: root.pixelSize
    }
}
