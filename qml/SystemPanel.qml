import QtQuick
import "."

// Hostname and OS on top, the avatar filling the middle, uptime / OS age and
// the shell at the bottom. Read once per opening. The avatar falls back to a
// glyph when none is configured or the image fails to load.
Card {
    id: root

    // Two columns under the avatar: UPTIME | OS AGE, SHELL | value.
    readonly property real columnWidth: (width - 3 * Config.cardPad) / 2

    component Rule: Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        height: 1
        color: Config.border
    }

    component Stat: Column {
        property string key
        property string value

        width: root.columnWidth
        spacing: Config.statGap

        Label {
            width: parent.width
            text: key
            font.pixelSize: Config.fontSizeSmall
        }

        Label {
            width: parent.width
            text: value
            color: value === Format.missing ? Config.fgDim : Config.fgActive
            font.pixelSize: Config.fontSizeLarge
        }
    }

    Column {
        id: header

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Config.statGap

        Label {
            width: parent.width
            text: Format.text(monitor.hostname)
            color: monitor.hostname === "" ? Config.fgDim : Config.fgActive
            font.pixelSize: Config.fontSizeLarge
        }

        Label {
            width: parent.width
            text: Format.text(monitor.osName)
            color: Config.fgDim
        }
    }

    Item {
        anchors.top: header.bottom
        anchors.bottom: statsRule.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.topMargin: Config.sectionGap
        anchors.bottomMargin: Config.sectionGap

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
            font.pixelSize: Config.avatarGlyphSize
        }
    }

    Rule {
        id: statsRule

        anchors.bottom: stats.top
        anchors.bottomMargin: Config.sectionGap
    }

    Row {
        id: stats

        anchors.bottom: shellRule.top
        anchors.bottomMargin: Config.sectionGap
        spacing: Config.cardPad

        Stat {
            key: "UPTIME"
            value: Format.uptime(monitor.uptime)
        }

        Stat {
            key: "OS AGE"
            value: Format.days(monitor.osAgeDays)
        }
    }

    Rule {
        id: shellRule

        anchors.bottom: shell.top
        anchors.bottomMargin: Config.sectionGap
    }

    Row {
        id: shell

        anchors.bottom: parent.bottom
        height: Config.shellRowHeight
        spacing: Config.cardPad

        Label {
            anchors.verticalCenter: parent.verticalCenter
            width: root.columnWidth
            text: "SHELL"
            font.pixelSize: Config.fontSizeSmall
        }

        Label {
            anchors.verticalCenter: parent.verticalCenter
            width: root.columnWidth
            text: Format.text(monitor.shellName)
            color: monitor.shellName === "" ? Config.fgDim : Config.fgActive
            font.pixelSize: Config.fontSizeMedium
        }
    }
}
