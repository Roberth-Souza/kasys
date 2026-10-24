import QtQuick
import ".."

// The units that held up the last boot (monitor.startupServices, slowest
// first, from systemd's critical chain): name, a bar scaled to the slowest
// one, and its time.
Card {
    id: root

    readonly property var units: monitor.startupServices.slice(0, Config.servicesRows)
    readonly property real slowest: units.length > 0 ? units[0].seconds : 0

    title: "Startup services"
    glyph: Config.glyphServices

    Label {
        id: subtitle

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: Config.servicesSubtitleHeight
        text: "What held up the boot"
        color: Config.fgDim
        font.pixelSize: Config.fontSizeSmall
    }

    Label {
        visible: root.units.length === 0
        anchors.centerIn: parent
        text: Format.missing
        color: Config.fgDim
    }

    Column {
        id: rows

        anchors.top: subtitle.bottom
        anchors.topMargin: Config.gap
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom

        Repeater {
            model: root.units

            Item {
                required property var modelData

                width: rows.width
                height: rows.height / Config.servicesRows

                Label {
                    id: name

                    anchors.verticalCenter: parent.verticalCenter
                    width: Config.servicesNameWidth
                    text: modelData.name
                    color: Config.fgActive
                }

                Bar {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: name.right
                    anchors.leftMargin: Config.gap
                    anchors.right: time.left
                    anchors.rightMargin: Config.gap
                    height: Config.servicesBarHeight
                    fraction: root.slowest > 0 ? modelData.seconds / root.slowest : -1
                }

                Label {
                    id: time

                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    width: Config.servicesTimeWidth
                    horizontalAlignment: Text.AlignRight
                    text: Format.seconds(modelData.seconds)
                }
            }
        }
    }
}
