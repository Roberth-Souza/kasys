import QtQuick
import ".."

// Stats side by side, split by vertical rules. Each cell gets its natural
// width plus an equal share of what is left; when the row is too narrow the
// cells shrink in proportion and elide. `stats` is a list of { key, value },
// plus an optional `note` (see Stat).
Item {
    id: root

    property var stats: []
    property int valueSize: Config.fontSizeMedium
    property int valueHeight: Config.partValueHeight

    readonly property real ruleSpace: 2 * Config.partStatGap + 1
    readonly property real natural: {
        let sum = 0;
        for (let i = 0; i < cells.count; i++)
            sum += cells.itemAt(i)?.stat.naturalWidth ?? 0;
        return sum;
    }
    readonly property real room: width - (cells.count - 1) * ruleSpace

    function cellWidth(naturalWidth) {
        if (room >= natural)
            return naturalWidth + (room - natural) / cells.count;
        return natural > 0 ? naturalWidth * room / natural : 0;
    }

    readonly property bool hasNote: stats.some(stat => (stat.note ?? "") !== "")

    implicitHeight: Config.partKeyHeight + valueHeight + (hasNote ? Config.partKeyHeight : 0)

    Row {
        height: parent.height

        Repeater {
            id: cells

            model: root.stats

            Item {
                required property var modelData
                required property int index
                readonly property alias stat: stat

                width: stat.x + stat.width
                height: parent.height

                Rectangle {
                    visible: index > 0
                    x: Config.partStatGap
                    width: 1
                    height: parent.height
                    color: Config.border
                }

                Stat {
                    id: stat

                    x: index > 0 ? root.ruleSpace : 0
                    width: root.cellWidth(naturalWidth)
                    key: modelData.key
                    value: modelData.value
                    note: modelData.note ?? ""
                    valueSize: root.valueSize
                    valueHeight: root.valueHeight
                }
            }
        }
    }
}
