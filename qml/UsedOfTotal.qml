import QtQuick
import "."

// "5.8 / 15.6 GiB" for a card heading: the used number white, the total grey.
Row {
    id: root

    property real used: -1
    property real total: -1

    readonly property var parts: Format.usedOfTotal(root.used, root.total)

    Label {
        text: root.parts.used
        color: Config.fgActive
    }

    Label {
        text: root.parts.total
    }
}
