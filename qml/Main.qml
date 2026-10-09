import QtQuick
import QtQuick.Window
import org.kde.layershell as LayerShell
import "."

// The window: a wlr-layer-shell overlay over the whole screen, transparent
// except for the fixed canvas centred in it. Same model as gitframe: open,
// glance, close (q, Escape, a click outside, or the launcher key again).
// Closing goes through `overlay`: a plain run quits, a daemon only hides.
Window {
    id: root

    visible: overlay.shown
    title: "kasys"
    color: "transparent"
    width: Screen.width
    height: Screen.height

    LayerShell.Window.scope: "kasys"
    LayerShell.Window.layer: LayerShell.Window.LayerOverlay
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityExclusive
    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom
                               | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
    LayerShell.Window.exclusionZone: -1

    // Qt does not always mark the layer surface active until the first input
    // event, and keys go nowhere until it does.
    Component.onCompleted: {
        if (root.visible)
            root.requestActivate();
    }
    onVisibleChanged: {
        if (root.visible)
            root.requestActivate();
    }
    onActiveChanged: {
        if (root.active)
            keyboard.forceActiveFocus();
    }

    MouseArea {
        anchors.fill: parent
        onClicked: overlay.close()
    }

    Shortcut {
        sequences: ["Q", "Escape"]
        onActivated: overlay.close()
    }

    Rectangle {
        id: canvas

        anchors.centerIn: parent
        width: Config.windowWidth
        height: Config.windowHeight
        color: Config.bg

        // Swallows clicks on the canvas, so only the transparent rest closes.
        MouseArea {
            anchors.fill: parent
        }

        Item {
            id: keyboard

            anchors.fill: parent
            focus: true

            Keys.onPressed: (event) => {
                switch (event.key) {
                case Qt.Key_J:
                case Qt.Key_Down:
                    sidebar.move(1);
                    break;
                case Qt.Key_K:
                case Qt.Key_Up:
                    sidebar.move(-1);
                    break;
                default:
                    return;
                }
                event.accepted = true;
            }

            Sidebar {
                id: sidebar

                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                anchors.margins: Config.pad
            }

            Item {
                id: content

                anchors.left: sidebar.right
                anchors.leftMargin: Config.blockGap
                anchors.right: parent.right
                anchors.rightMargin: Config.pad
                anchors.top: parent.top
                anchors.topMargin: Config.pad
                height: Config.contentHeight

                Overview {
                    anchors.fill: parent
                    visible: sidebar.activeTab === 1
                }

                PlaceholderPage {
                    anchors.fill: parent
                    visible: sidebar.activeTab !== 1
                    name: sidebar.tabs[sidebar.activeTab].name
                    pageGlyph: sidebar.tabs[sidebar.activeTab].glyph
                }
            }
        }
    }
}
