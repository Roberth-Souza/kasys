import QtQuick
import "."

// Avatar and system info, read once per opening. The avatar is a placeholder
// until its config reader lands; the space under the rule is reserved for
// the quote.
Card {
    Row {
        id: top

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Config.cardPad

        Rectangle {
            width: Config.avatarWidth
            height: Config.avatarHeight
            color: Config.clear
            border.color: Config.border
            border.width: 1

            Label {
                anchors.centerIn: parent
                text: Config.glyphAvatar
                color: Config.fgDim
                font.pixelSize: 2 * Config.glyphSize
            }
        }

        Column {
            id: info

            width: top.width - Config.avatarWidth - top.spacing

            Repeater {
                model: [
                    { "key": "Hostname", "value": Format.text(monitor.hostname) },
                    { "key": "OS", "value": Format.text(monitor.osName) },
                    { "key": "Uptime", "value": Format.uptime(monitor.uptime) },
                    { "key": "Installed", "value": Format.text(monitor.installDate) }
                ]

                Row {
                    required property var modelData

                    width: info.width
                    height: Config.infoRowHeight

                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        width: Config.infoKeyWidth
                        text: modelData.key
                    }

                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        width: info.width - Config.infoKeyWidth
                        text: modelData.value
                        color: modelData.value === Format.missing ? Config.fgDim : Config.fgActive
                    }
                }
            }
        }
    }

    Rectangle {
        anchors.top: top.bottom
        anchors.topMargin: Config.cardPad
        anchors.left: parent.left
        anchors.right: parent.right
        height: 1
        color: Config.border
    }
}
