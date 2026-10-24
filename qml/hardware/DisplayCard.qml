import QtQuick
import QtQuick.Window
import ".."
import "art.js" as Art

// The screen the window is on: QML's Screen gives the resolution (scaled
// back to device pixels), connector and monitor name, the bridge the
// refresh rate.
PartCard {
    readonly property string monitorName: [Screen.manufacturer, Screen.model].filter(part => part).join(" ")

    art: Art.monitor()
    artWidth: Config.artMonitorWidth

    PartTitle {
        width: parent.width
        title: "Display"
        name: Math.round(Screen.width * Screen.devicePixelRatio) + " × "
              + Math.round(Screen.height * Screen.devicePixelRatio)
        detail: Format.hz(monitor.refreshRate(Screen.name)) + " · " + Format.connector(Screen.name)
    }

    PartRule {
        width: parent.width
    }

    // The diagonal comes from EDID: no collector yet.
    PartPairs {
        width: parent.width
        rows: [{ "label": "Monitor", "value": Format.text(monitorName), "pending": true }]
    }
}
