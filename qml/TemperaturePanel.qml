import QtQuick
import "."

// One row per hwmon chip, one sensor each (picked by the bridge).
Card {
    id: root

    // The GPU is drawn (GpuIcon), not a glyph.
    readonly property var glyphs: ({
        "cpu": Config.glyphCpu,
        "disk": Config.glyphDisk
    })

    title: "Temperatures"
    glyph: Config.glyphTemperature

    Column {
        anchors.fill: parent

        Repeater {
            model: monitor.temperatures

            Item {
                id: entry

                required property var modelData

                width: parent.width
                height: Config.temperatureRowHeight

                Row {
                    height: parent.height
                    spacing: Config.gap

                    Item {
                        width: Config.iconWidth
                        height: parent.height

                        GpuIcon {
                            visible: entry.modelData.kind === "gpu"
                            anchors.centerIn: parent
                        }

                        Label {
                            visible: entry.modelData.kind !== "gpu"
                            anchors.fill: parent
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            elide: Text.ElideNone
                            text: root.glyphs[entry.modelData.kind] ?? Config.glyphTemperature
                            font.pixelSize: Config.iconSize
                        }
                    }

                    Label {
                        height: parent.height
                        verticalAlignment: Text.AlignVCenter
                        text: entry.modelData.name.toUpperCase()
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
