import QtQuick
import "."

// The busiest processes, picked and sorted by the bridge. Shows as many rows
// as the card has room for.
Card {
    id: root

    title: "Running Processes"
    glyph: Config.glyphProcesses

    headerRight: Label {
        text: "Top by memory"
        color: Config.fgDim
    }

    component ProcessRow: Row {
        property string pid: Format.missing
        property string cpu: Format.missing
        property string mem: Format.missing
        property string name: Format.missing
        property color textColor: Config.fg

        height: Config.processRowHeight

        Label {
            width: Config.pidWidth
            text: pid
            color: textColor
        }

        Label {
            width: Config.processPercentWidth
            text: cpu
            color: textColor
        }

        Label {
            width: Config.processMemWidth
            text: mem
            color: textColor
        }

        Label {
            width: Config.columnInner - Config.pidWidth - Config.processPercentWidth
                   - Config.processMemWidth
            text: name
            color: textColor
        }
    }

    Column {
        id: table

        // Column labels and the gap under them excluded.
        readonly property int fittingRows: Math.max(0, Math.floor(
            (height - Config.processRowHeight - Config.processHeaderGap)
            / Config.processRowHeight))

        anchors.fill: parent
        anchors.topMargin: Config.processTableTop
        clip: true

        ProcessRow {
            pid: "PID"
            cpu: "CPU%"
            mem: "MEM"
            name: "Name"
            textColor: Config.fgDim
        }

        Item {
            width: 1
            height: Config.processHeaderGap
        }

        Repeater {
            model: monitor.topProcesses.slice(0, table.fittingRows)

            ProcessRow {
                required property var modelData

                pid: modelData.pid
                cpu: modelData.cpu.toFixed(1)
                mem: Format.bytes(modelData.mem)
                name: modelData.name
            }
        }

        ProcessRow {
            visible: monitor.topProcesses.length === 0
            textColor: Config.fgDim
        }
    }
}
