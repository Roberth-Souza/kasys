import QtQuick
import ".."

// Which part this is: the heading, the name in big type, and an
// optional detail line under it.
Column {
    id: root

    property string title: ""
    property string name: Format.notBuilt
    property bool hasDetail: true
    property string detail: ""
    property bool detailPending: false

    Label {
        width: root.width
        height: Config.partHeadHeight
        verticalAlignment: Text.AlignVCenter
        text: root.title
        color: Config.fgActive
    }

    Label {
        width: root.width
        height: Config.partNameHeight
        verticalAlignment: Text.AlignVCenter
        text: root.name
        color: Format.absent(root.name) ? Config.fgDim : Config.fgActive
        font.pixelSize: Config.fontSizeLarge
    }

    PendingText {
        visible: root.hasDetail
        width: root.width
        height: Config.partSubHeight
        text: root.detail
        pending: root.detailPending
    }
}
