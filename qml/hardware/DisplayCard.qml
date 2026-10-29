import QtQuick
import QtQuick.Window
import ".."
import "art.js" as Art
import "specs.js" as Specs

// The screen the window is on: QML's Screen gives the resolution (scaled
// back to device pixels), connector and monitor name, the bridge the
// refresh rate and the diagonal.
PartCard {
    readonly property string monitorName: [Screen.manufacturer, Screen.model].filter(part => part).join(" ")
    readonly property real diagonal: monitor.monitorDiagonal(Screen.name)
    // "AOC 2460G4 · 24\"": either half may be missing (no EDID size, no name).
    readonly property string monitorText: [monitorName, diagonal < 0 ? "" : Format.inches(diagonal)]
        .filter(part => part).join(" · ")

    readonly property int pixelWidth: Math.round(Screen.width * Screen.devicePixelRatio)
    readonly property int pixelHeight: Math.round(Screen.height * Screen.devicePixelRatio)

    art: Art.monitor()
    artWidth: Config.artMonitorWidth

    PartTitle {
        width: parent.width
        title: "Display"
        name: pixelWidth + " × " + pixelHeight
        detail: Format.hz(monitor.refreshRate(Screen.name)) + " · " + Format.connector(Screen.name)
    }

    PartRule {
        width: parent.width
    }

    PartPairs {
        width: parent.width
        rows: [{ "label": "Monitor", "value": Format.text(monitorText) }]
    }

    // The whole page's specs, here because only this card has QML's Screen.
    corner: CopyButton {
        label: "Copy hardware specs"
        build: () => Specs.hardware(monitor, Format, {
            "monitor": [monitorName, diagonal < 0 ? "" : Format.inches(diagonal)].filter(part => part).join(" "),
            "width": pixelWidth,
            "height": pixelHeight,
            "hz": monitor.refreshRate(Screen.name),
            "connector": Format.connector(Screen.name)
        })
    }
}
