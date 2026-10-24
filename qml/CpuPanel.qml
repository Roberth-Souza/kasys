import QtQuick
import "."

// Total usage graph, the model and its core counts, current total and peak
// over the graph's span, then the busiest processes by CPU.
Card {
    id: root

    // Seconds of history behind the peak: under a minute right
    // after launch, so the label never claims more than it has.
    readonly property string span: monitor.cpuHistory.length + "s"

    function count(n, unit) { return n < 0 ? Format.missing : n + " " + unit; }

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

    component Stat: Column {
        property string label: ""
        property string value: Format.missing
        property color valueColor: Config.fgActive

        Label {
            width: parent.width
            height: Config.cpuStatLabelHeight
            text: label
            color: Config.fgDim
        }

        Label {
            width: parent.width
            text: value
            color: valueColor
            font.pixelSize: Config.fontSizeLarge
        }
    }

    component ProcessRow: Item {
        property string name: Format.missing
        property string cpu: ""
        property color nameColor: Config.fg
        property color cpuColor: Config.fgActive

        height: Config.processRowHeight

        Label {
            anchors.left: parent.left
            anchors.right: cpuText.left
            anchors.rightMargin: Config.gap
            anchors.verticalCenter: parent.verticalCenter
            text: name
            color: nameColor
        }

        Label {
            id: cpuText

            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            text: cpu
            color: cpuColor
        }
    }

    Column {
        anchors.fill: parent
        spacing: Config.sectionGap

        Graph {
            width: parent.width
            height: Config.cpuGraphHeight
            values: monitor.cpuHistory
        }

        Column {
            width: parent.width

            Label {
                width: parent.width
                height: Config.cpuModelHeight
                text: Format.text(monitor.cpuModel)
                color: Config.fgActive
                font.pixelSize: Config.fontSizeMedium
            }

            Label {
                width: parent.width
                height: Config.cpuCoresHeight
                text: root.count(monitor.cpuCores, "cores") + " / "
                      + root.count(monitor.cpuThreads, "threads")
            }
        }

        Item {
            width: parent.width
            height: Config.cpuStatHeight

            Stat {
                anchors.left: parent.left
                width: parent.width / 2 - Config.cardPad
                label: "TOTAL"
                value: Format.percent(monitor.cpuUsage)
            }

            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                width: 1
                height: parent.height - Config.gap
                color: Config.border
            }

            Stat {
                anchors.right: parent.right
                width: parent.width / 2 - Config.cardPad
                label: "PEAK · " + root.span
                value: Format.percent(monitor.cpuPeak)
                valueColor: Config.fg
            }
        }

        Column {
            width: parent.width

            ProcessRow {
                width: parent.width
                name: "TOP BY CPU"
                cpu: "CPU"
                nameColor: Config.fgDim
                cpuColor: Config.fgDim
            }

            Repeater {
                model: monitor.topCpuProcesses

                ProcessRow {
                    required property var modelData

                    width: parent.width
                    name: modelData.name
                    cpu: modelData.cpu.toFixed(1) + "%"
                }
            }

            ProcessRow {
                visible: monitor.topCpuProcesses.length === 0
                width: parent.width
                nameColor: Config.fgDim
            }
        }
    }
}
