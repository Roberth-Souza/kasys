import QtQuick
import "."

// Total usage graph, then one row per thread. The per-thread readings have
// no collector yet, so those rows hold "--" and an empty bar.
Card {
    title: "CPU"
    glyph: Config.glyphCpu

    headerRight: Row {
        spacing: Config.blockGap

        Label {
            text: Format.percent(monitor.cpuUsage)
            color: Config.fgActive
        }

        Label {
            text: Format.ghz(monitor.cpuFreq)
        }
    }

    Graph {
        id: graph

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: Config.cpuGraphHeight
        values: monitor.cpuHistory
    }

    Grid {
        id: cores

        readonly property int cellWidth: (width - Config.coreColumnGap) / 2

        anchors.top: graph.bottom
        anchors.topMargin: Config.sectionGap
        anchors.left: parent.left
        anchors.right: parent.right
        columns: 2
        flow: Grid.TopToBottom
        rows: Config.coreRows
        columnSpacing: Config.coreColumnGap

        Repeater {
            model: Math.min(monitor.coreCount, 2 * Config.coreRows)

            Item {
                required property int index

                width: cores.cellWidth
                height: Config.coreRowHeight

                Label {
                    id: coreName

                    anchors.verticalCenter: parent.verticalCenter
                    width: Config.coreLabelWidth
                    text: "Core " + index
                    font.pixelSize: Config.fontSizeSmall
                }

                Label {
                    id: corePercent

                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: coreName.right
                    width: Config.corePercentWidth
                    text: Format.missing
                    color: Config.fgDim
                    font.pixelSize: Config.fontSizeSmall
                }

                Bar {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: corePercent.right
                    anchors.right: parent.right
                }
            }
        }
    }
}
