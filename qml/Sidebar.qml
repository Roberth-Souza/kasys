import QtQuick
import "."

// The left column: the app mark, then the page tabs. `activeTab` is the page
// on show; j/k in Main.qml and a click here both move it.
Card {
    id: root

    property int activeTab: 1

    readonly property var tabs: [
        { "name": "System", "glyph": Config.glyphSystem },
        { "name": "Overview", "glyph": Config.glyphOverview },
        { "name": "Processes", "glyph": Config.glyphProcesses },
        { "name": "Hardware", "glyph": Config.glyphChip },
        { "name": "Storage", "glyph": Config.glyphDisk }
    ]

    function move(delta) {
        root.activeTab = Math.max(0, Math.min(root.tabs.length - 1, root.activeTab + delta));
    }

    width: Config.sidebarWidth

    Row {
        id: mark

        anchors.top: parent.top
        anchors.left: parent.left
        spacing: Config.gap

        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: Config.glyphApp
            color: Config.fgActive
            font.pixelSize: Config.fontSizeMedium
        }

        Column {
            anchors.verticalCenter: parent.verticalCenter

            Label {
                text: "kasys"
                color: Config.fgActive
                font.pixelSize: Config.fontSizeMedium
            }

            Label {
                text: monitor.hostname
                color: Config.fgDim
                font.pixelSize: Config.fontSizeSmall
            }
        }
    }

    Rectangle {
        id: rule

        anchors.top: mark.bottom
        anchors.topMargin: Config.ruleGap
        anchors.left: parent.left
        anchors.right: parent.right
        height: 1
        color: Config.border
    }

    Column {
        anchors.top: rule.bottom
        anchors.topMargin: Config.ruleGap
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Config.gap

        Repeater {
            model: root.tabs

            Rectangle {
                required property int index
                required property var modelData

                readonly property bool active: index === root.activeTab

                width: parent.width
                height: Config.tabHeight
                color: active ? Config.activeFill : Config.clear
                radius: Config.radius

                Behavior on color {
                    ColorAnimation { duration: Config.animFast }
                }

                Row {
                    anchors.left: parent.left
                    anchors.leftMargin: Config.sidebarRowPadX
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: Config.gap

                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        width: Config.sidebarGlyphWidth
                        horizontalAlignment: Text.AlignHCenter
                        text: modelData.glyph
                        color: active ? Config.fgInvert : Config.fg
                        font.pixelSize: Config.sidebarGlyphSize
                    }

                    Label {
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.name
                        color: active ? Config.fgInvert : Config.fg
                    }
                }

                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.activeTab = index
                }
            }
        }
    }
}
