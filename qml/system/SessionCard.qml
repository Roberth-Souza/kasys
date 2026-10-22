import QtQuick
import QtQuick.Window
import ".."

// Desktop, display server and shell on the left, the screen on the right.
// Resolution comes from QML's Screen (scaled back to device pixels), the
// refresh rate from the bridge.
PairCard {
    title: "Desktop & session"
    glyph: Config.glyphSession

    leftRows: [
        { "label": "Desktop", "value": Format.text(monitor.desktop) },
        { "label": "Display server", "value": Format.displayServer(monitor.displayServer) },
        { "label": "Shell", "value": Format.text(monitor.shellName) }
    ]
    rightRows: [
        {
            "label": "Resolution",
            "value": Math.round(Screen.width * Screen.devicePixelRatio) + " × "
                     + Math.round(Screen.height * Screen.devicePixelRatio)
        },
        { "label": "Refresh rate", "value": Format.hz(monitor.refreshRate(Screen.name)) }
    ]
}
