import QtQuick
import "."

// A button that puts `build()` on the clipboard, then says "Copied" for a
// moment. The owner builds the text only when clicked. Made for a card's
// bottom-right corner: it draws only its top and left edges, the card's
// border is the other two.
Item {
    id: root

    property string label: ""
    property var build: () => ""

    property bool copied: false

    implicitWidth: content.width + 2 * Config.buttonPadX
    implicitHeight: Config.buttonHeight
    width: implicitWidth
    height: implicitHeight

    Rectangle {
        width: parent.width
        height: Config.cardBorderWidth
        color: Config.border
    }

    Rectangle {
        width: Config.cardBorderWidth
        height: parent.height
        color: Config.border
    }

    Row {
        id: content

        anchors.centerIn: parent
        spacing: Config.gap

        Label {
            anchors.verticalCenter: parent.verticalCenter
            text: root.copied ? Config.glyphCheck : Config.glyphCopy
            color: Config.fgActive
            font.pixelSize: Config.glyphSize
        }

        Label {
            id: caption

            anchors.verticalCenter: parent.verticalCenter
            // Sized for the label, so "Copied" does not shift the button.
            width: Math.ceil(labelMetrics.advanceWidth)
            text: root.copied ? "Copied" : root.label
            color: Config.fgActive
        }
    }

    TextMetrics {
        id: labelMetrics

        font: caption.font
        text: root.label
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            monitor.copyToClipboard(root.build());
            root.copied = true;
            reset.restart();
        }
    }

    Timer {
        id: reset

        interval: Config.copiedMs
        onTriggered: root.copied = false
    }
}
