import QtQuick
import "."

// Avatar and system info, read once per opening. The avatar falls back to a
// glyph when none is configured or the image fails to load; the space under
// the rule is reserved for the quote.
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
            // The frame only outlines the placeholder glyph.
            border.width: avatar.status === Image.Ready ? 0 : 1

            Image {
                id: avatar

                anchors.fill: parent
                source: monitor.avatarUrl
                fillMode: Image.PreserveAspectFit
                asynchronous: true
                smooth: true
                mipmap: true
                // Decode near box size instead of keeping the full image.
                sourceSize.width: 2 * width
                sourceSize.height: 2 * height
            }

            Label {
                visible: avatar.status !== Image.Ready
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
                    { "key": "OS age", "value": Format.days(monitor.osAgeDays) }
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
