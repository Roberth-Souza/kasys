import QtQuick
import ".."

// A half-width hardware card: drawing | identity, no rule between.
Card {
    id: root

    property alias art: drawing.art
    property alias artWidth: drawing.width
    default property alias identity: identityColumn.data

    Item {
        id: artCell

        width: Config.partSplitArtWidth
        height: parent.height

        LineArt {
            id: drawing

            anchors.centerIn: parent
        }
    }

    Column {
        id: identityColumn

        anchors.left: artCell.right
        anchors.leftMargin: Config.cardPad
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
    }
}
