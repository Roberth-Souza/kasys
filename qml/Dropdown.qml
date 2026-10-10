import QtQuick
import QtQuick.Controls.Basic
import "."

// The current option with a chevron; a click lists every option under it.
// Picking one emits `picked`; the owner decides what `current` becomes.
Item {
    id: root

    property var options: []
    property string current: ""

    signal picked(string option)

    width: button.width
    height: parent ? parent.height : Config.cardTitleHeight

    Row {
        id: button

        anchors.verticalCenter: parent.verticalCenter
        spacing: Config.gap

        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: root.current === "" ? Format.missing : root.current
            color: root.current === "" ? Config.fgDim : Config.fgActive
        }

        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: Config.glyphChevronDown
            font.pixelSize: Config.glyphSize
        }
    }

    MouseArea {
        anchors.fill: parent
        enabled: root.options.length > 0
        cursorShape: Qt.PointingHandCursor
        onClicked: menu.visible ? menu.close() : menu.open()
    }

    Popup {
        id: menu

        y: root.height
        padding: 1

        background: Rectangle {
            color: Config.menuBg
            border.color: Config.border
            border.width: 1
        }

        contentItem: Column {
            Repeater {
                model: root.options

                Rectangle {
                    id: option

                    required property string modelData
                    readonly property bool active: modelData === root.current

                    width: Config.dropdownWidth
                    height: Config.tabHeight
                    color: active ? Config.activeFill : hover.containsMouse ? Config.hoverFill : Config.clear

                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: parent.left
                        anchors.leftMargin: Config.sidebarRowPadX
                        text: option.modelData
                        color: option.active ? Config.fgInvert : Config.fg
                    }

                    MouseArea {
                        id: hover

                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            root.picked(option.modelData);
                            menu.close();
                        }
                    }
                }
            }
        }
    }
}
