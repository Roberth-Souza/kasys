import QtQuick
import ".."

// A card with two PairColumns side by side, split by a vertical rule.
Card {
    id: root

    property var leftRows: []
    property var rightRows: []

    readonly property real columnWidth: (width - 2 * Config.cardPad - 1 - 2 * Config.cardPad) / 2

    PairColumn {
        id: left

        width: root.columnWidth
        rows: root.leftRows
    }

    Rectangle {
        id: divider

        anchors.left: left.right
        anchors.leftMargin: Config.cardPad
        width: 1
        height: Config.pairRows * Config.pairRowHeight
        color: Config.border
    }

    PairColumn {
        anchors.left: divider.right
        anchors.leftMargin: Config.cardPad
        width: root.columnWidth
        rows: root.rightRows
    }
}
