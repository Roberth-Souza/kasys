import QtQuick
import ".."

// A half-width hardware card: drawing | identity, no rule between.
Card {
    id: root

    property alias art: drawing.art
    property alias artWidth: drawing.width
    default property alias identity: identityColumn.data
    // Bottom right, against the card's border (the copy button).
    property alias corner: cornerSlot.data

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

    Item {
        id: cornerSlot

        anchors.right: parent.right
        anchors.bottom: parent.bottom
        // Out of the card's padding, up to the inside of its border.
        anchors.rightMargin: Config.cardBorderWidth - Config.cardPad
        anchors.bottomMargin: Config.cardBorderWidth - root.bottomPad
        width: childrenRect.width
        height: childrenRect.height
    }
}
