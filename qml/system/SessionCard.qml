import QtQuick
import QtQuick.Window
import ".."

// Desktop, display and shell. Resolution comes from QML's Screen (scaled
// back to device pixels), the refresh rate from the bridge.
Card {
    title: "Desktop & session"
    glyph: Config.glyphSession

    Column {
        anchors.left: parent.left
        anchors.right: parent.right

        InfoRow {
            width: parent.width
            label: "Desktop"
            value: Format.text(monitor.desktop)
        }

        InfoRow {
            width: parent.width
            label: "Display server"
            value: Format.displayServer(monitor.displayServer)
        }

        InfoRow {
            width: parent.width
            label: "Shell"
            value: Format.text(monitor.shellName)
        }

        InfoRow {
            width: parent.width
            label: "Resolution"
            value: Math.round(Screen.width * Screen.devicePixelRatio) + " × "
                   + Math.round(Screen.height * Screen.devicePixelRatio)
        }

        InfoRow {
            width: parent.width
            label: "Refresh rate"
            value: Format.hz(monitor.refreshRate(Screen.name))
        }
    }
}
