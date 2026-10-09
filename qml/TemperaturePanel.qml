import QtQuick
import "."

// Placeholder until the sensors collector (M4): one row per sensor, "--°C".
Card {
    title: "Temperatures"
    glyph: Config.glyphTemperature

    Column {
        anchors.fill: parent

        Repeater {
            model: [
                { "name": "CPU (Tctl)", "glyph": Config.glyphChip },
                { "name": "CPU (CCD)", "glyph": Config.glyphChip },
                { "name": "GPU", "glyph": Config.glyphGpu },
                { "name": "GPU Hot Spot", "glyph": Config.glyphGpu },
                { "name": "NVMe", "glyph": Config.glyphDisk }
            ]

            Item {
                required property var modelData

                width: parent.width
                height: Config.temperatureRowHeight

                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: Config.gap

                    Label {
                        text: modelData.glyph
                        font.pixelSize: Config.glyphSize
                    }

                    Label {
                        text: modelData.name
                    }
                }

                Label {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: Format.missing + "°C"
                    color: Config.fgDim
                }
            }
        }
    }
}
