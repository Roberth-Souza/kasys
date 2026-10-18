import QtQuick
import "."

// Name under the title, utilization (big number + graph), VRAM bar, then
// TEMP | CLOCK | FAN. Every value is "--" without an amdgpu card.
Card {
    id: root

    readonly property real vramPercent: monitor.gpuVramTotal > 0
                                        ? 100 * monitor.gpuVramUsed / monitor.gpuVramTotal
                                        : -1

    title: "GPU"
    icon: GpuIcon {}

    headerRight: Label {
        text: Format.percent(monitor.gpuUsage)
        color: Config.fgActive
    }

    component Rule: Rectangle {
        color: Config.border
    }

    component Stat: Column {
        property string key
        property string value

        spacing: Config.statGap

        Label {
            width: parent.width
            text: key
            color: Config.fgDim
            font.pixelSize: Config.fontSizeSmall
        }

        Label {
            width: parent.width
            text: value
            color: value === Format.missing ? Config.fgDim : Config.fgActive
            font.pixelSize: Config.fontSizeMedium
        }
    }

    Column {
        anchors.fill: parent
        spacing: Config.sectionGap

        // Indented to start under the title text, past the icon cell.
        Label {
            x: Config.iconWidth + Config.gap
            width: parent.width - x
            height: Config.gpuNameHeight
            text: Format.text(monitor.gpuName)
            color: Config.fgDim
        }

        Item {
            width: parent.width
            height: Config.gpuGraphHeight + Config.gpuSpanHeight

            Column {
                anchors.left: parent.left
                anchors.verticalCenter: usageRule.verticalCenter
                width: Config.gpuUsageWidth - Config.gap
                spacing: Config.statGap

                Label {
                    width: parent.width
                    text: Format.percent(monitor.gpuUsage)
                    color: monitor.gpuUsage < 0 ? Config.fgDim : Config.fgActive
                    font.pixelSize: Config.fontSizeHuge
                }

                Label {
                    width: parent.width
                    text: "UTILIZATION"
                    color: Config.fgDim
                    font.pixelSize: Config.fontSizeSmall
                }
            }

            Rule {
                id: usageRule

                x: Config.gpuUsageWidth
                width: 1
                height: Config.gpuGraphHeight
            }

            Graph {
                id: usageGraph

                anchors.left: usageRule.right
                anchors.leftMargin: Config.gap
                anchors.right: parent.right
                height: Config.gpuGraphHeight
                values: monitor.gpuHistory
            }

            Label {
                anchors.right: parent.right
                anchors.top: usageGraph.bottom
                height: Config.gpuSpanHeight
                verticalAlignment: Text.AlignBottom
                text: Config.historyLength + "s"
                color: Config.fgDim
                font.pixelSize: Config.fontSizeSmall
            }
        }

        Column {
            width: parent.width
            spacing: Config.gap

            Item {
                width: parent.width
                height: Config.meterRowHeight

                Label {
                    anchors.left: parent.left
                    anchors.verticalCenter: parent.verticalCenter
                    text: "VRAM"
                }

                UsedOfTotal {
                    anchors.centerIn: parent
                    used: monitor.gpuVramUsed
                    total: monitor.gpuVramTotal
                }

                Label {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: Format.percent(root.vramPercent)
                    color: root.vramPercent < 0 ? Config.fgDim : Config.fgActive
                }
            }

            Bar {
                width: parent.width
                height: Config.gpuVramBarHeight
                fraction: root.vramPercent < 0 ? -1 : root.vramPercent / 100
            }
        }

        Rule {
            width: parent.width
            height: 1
        }

        // Three equal columns split by 1px rules.
        Row {
            id: stats

            readonly property real columnWidth: (width - 2 * (2 * Config.cardPad + 1)) / 3

            width: parent.width
            height: Config.gpuStatHeight
            spacing: Config.cardPad

            Stat {
                width: stats.columnWidth
                key: "TEMP"
                value: Format.celsius(monitor.gpuTemp)
            }

            Rule {
                width: 1
                height: parent.height
            }

            Stat {
                width: stats.columnWidth
                key: "CLOCK"
                value: Format.mhz(monitor.gpuClock)
            }

            Rule {
                width: 1
                height: parent.height
            }

            Stat {
                width: stats.columnWidth
                key: "FAN"
                value: Format.rpm(monitor.gpuFan)
            }
        }
    }
}
