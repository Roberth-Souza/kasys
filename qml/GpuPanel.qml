import QtQuick
import "."

// Placeholder until the GPU collector (M5): the full layout, every value "--".
Card {
    title: "GPU"
    glyph: Config.glyphGpu

    headerRight: Row {
        spacing: Config.blockGap

        Label {
            text: Format.missing
            color: Config.fgDim
        }

        Label {
            text: Format.missing + " MHz"
            color: Config.fgDim
        }
    }

    Column {
        anchors.fill: parent
        spacing: Config.sectionGap

        Graph {
            width: parent.width
            height: Config.graphHeight
        }

        Column {
            width: parent.width
            spacing: Config.gap

            Label {
                width: parent.width
                height: Config.gpuNameHeight
                text: Format.missing
                color: Config.fgDim
            }

            Column {
                width: parent.width

                Repeater {
                    model: ["GPU", "VRAM", "Temperature", "Fan"]

                    MeterRow {
                        required property string modelData

                        width: parent.width
                        height: Config.gpuRowHeight
                        label: modelData
                    }
                }
            }
        }
    }
}
