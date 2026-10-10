import QtQuick
import "."

// The bordered black box every block sits in: 1px border, square corners, no
// shadow. Heading row: glyph + title + `headerLeft` on the left, `headerRight`
// on the right.
Rectangle {
    id: root

    property string title: ""
    property string glyph: ""
    default property alias content: body.data
    property alias headerLeft: extra.data
    property alias headerRight: controls.data

    color: Config.cardBg
    border.color: Config.border
    border.width: 1
    radius: 0

    Row {
        id: heading

        visible: root.title !== ""
        height: visible ? Config.cardTitleHeight : 0
        spacing: Config.gap
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.margins: Config.cardPad

        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: root.glyph
            font.pixelSize: Config.glyphSize
        }

        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: root.title
            color: Config.fgActive
        }

        Item {
            id: extra

            anchors.verticalCenter: parent.verticalCenter
            width: childrenRect.width
            height: parent.height
        }
    }

    Item {
        id: controls

        anchors.top: parent.top
        anchors.right: parent.right
        anchors.margins: Config.cardPad
        height: heading.visible ? Config.cardTitleHeight : 0
        width: childrenRect.width
    }

    Item {
        id: body

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.top: heading.visible ? heading.bottom : parent.top
        anchors.margins: Config.cardPad
        anchors.topMargin: heading.visible ? Config.titleGap : Config.cardPad
    }
}
