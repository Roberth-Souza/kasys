import QtQuick
import ".."

// A full-width hardware row: drawing | identity | live, split by vertical
// rules. `identity` and `live` stack their children, centred vertically.
Card {
    id: root

    property alias art: drawing.art
    property alias artColor: drawing.color
    property alias artWidth: drawing.width
    default property alias identity: identityColumn.data
    property alias live: liveColumn.data

    Item {
        id: artCell

        width: Config.partArtWidth
        height: parent.height

        LineArt {
            id: drawing

            anchors.centerIn: parent
        }
    }

    Rectangle {
        id: firstRule

        x: artCell.width + Config.partColumnGap
        width: 1
        height: parent.height
        color: Config.border
    }

    Column {
        id: identityColumn

        anchors.left: firstRule.right
        anchors.leftMargin: Config.partColumnGap
        anchors.right: secondRule.left
        anchors.rightMargin: Config.partColumnGap
        anchors.verticalCenter: parent.verticalCenter
    }

    Rectangle {
        id: secondRule

        anchors.right: liveColumn.left
        anchors.rightMargin: Config.partColumnGap
        width: 1
        height: parent.height
        color: Config.border
    }

    Column {
        id: liveColumn

        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        width: Config.partLiveWidth
    }
}
