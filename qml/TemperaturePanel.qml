import QtQuick
import "."

// One row per hwmon chip, one sensor each (picked by the bridge).
Card {
    id: root

    readonly property var glyphs: ({
        "cpu": Config.glyphChip,
        "gpu": Config.glyphGpu,
        "disk": Config.glyphDisk
    })

    title: "Temperatures"
    glyph: Config.glyphTemperature

    Column {
        anchors.fill: parent

        Repeater {
            model: monitor.temperatures

            Item {
                required property var modelData

                width: parent.width
                height: Config.temperatureRowHeight

                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: Config.gap

                    Label {
                        text: root.glyphs[modelData.kind] ?? Config.glyphTemperature
                        font.pixelSize: Config.glyphSize
                    }

                    Label {
                        text: modelData.name
                    }
                }

                Label {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: Math.round(modelData.celsius) + "°C"
                    color: Config.fgActive
                }
            }
        }

        Label {
            visible: monitor.temperatures.length === 0
            height: Config.temperatureRowHeight
            verticalAlignment: Text.AlignVCenter
            text: Format.missing + "°C"
            color: Config.fgDim
        }
    }
}
