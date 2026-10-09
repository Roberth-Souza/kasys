import QtQuick
import "."

// Placeholder until the process collector (M4): header and empty rows.
Card {
    id: root

    title: "Running Processes"
    glyph: Config.glyphProcesses

    headerRight: Label {
        text: "Top by CPU"
        color: Config.fgDim
    }

    component ProcessRow: Row {
        property string pid: Format.missing
        property string cpu: Format.missing
        property string mem: Format.missing
        property string command: Format.missing
        property color textColor: Config.fgDim

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
            width: Config.processPercentWidth
            text: mem
            color: textColor
        }

        Label {
            width: Config.columnInner - Config.pidWidth - 2 * Config.processPercentWidth
            text: command
            color: textColor
        }
    }

    Column {
        anchors.fill: parent

        ProcessRow {
            pid: "PID"
            cpu: "CPU%"
            mem: "MEM%"
            command: "Command"
            textColor: Config.fg
        }

        Repeater {
            model: Config.processRows

            ProcessRow {}
        }
    }
}
