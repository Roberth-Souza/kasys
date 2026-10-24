import QtQuick
import ".."

// A horizontal rule with room above and below.
Item {
    height: 2 * Config.partRuleGap + 1

    Rectangle {
        anchors.verticalCenter: parent.verticalCenter
        width: parent.width
        height: 1
        color: Config.border
    }
}
