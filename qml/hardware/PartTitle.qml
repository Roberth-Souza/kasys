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
    // Optional control beside the heading, e.g. a Dropdown.
    property Component picker: null

    Row {
        width: root.width
        height: Config.partHeadHeight
        spacing: Config.blockGap

        Label {
            height: parent.height
            verticalAlignment: Text.AlignVCenter
            text: root.title
            color: Config.fgActive
        }

        Loader {
            height: parent.height
            sourceComponent: root.picker
        }
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
