import QtQuick
import ".."
import "art.js" as Art

// Name, VRAM and bus beside the card, its three temperatures, fan and power
// live.
PartRow {
    art: Art.gpu()
    artWidth: Config.artGpuWidth
    bottomPad: Config.hwGpuBottomPad

    PartTitle {
        width: parent.width
        title: "Graphics"
        name: Format.text(monitor.gpuName)
        detail: monitor.gpuVramTotal < 0 ? Format.missing
            : Format.bytes(monitor.gpuVramTotal) + " VRAM" + (monitor.gpuVramType === "" ? "" : " · " + monitor.gpuVramType)
    }

    PartRule {
        width: parent.width
    }

    StatRow {
        width: parent.width
        stats: [
            {
                "key": "Interface",
                "value": Format.pcieLink(monitor.gpuLinkSpeed, monitor.gpuLinkWidth),
                "note": Format.pcieCardNote(monitor.gpuLinkSpeed, monitor.gpuLinkWidth,
                                            monitor.gpuCardSpeed, monitor.gpuCardWidth)
            },
            { "key": "Mesa", "value": Format.text(monitor.mesaVersion) },
            { "key": "Driver", "value": Format.text(monitor.gpuDriver) }
        ]
    }

    live: [
        StatRow {
            width: parent.width
            valueSize: Config.fontSizeLarge
            valueHeight: Config.partMidHeight
            stats: [
                { "key": "Core", "value": Format.celsius(monitor.gpuTemp) },
                { "key": "Hotspot", "value": Format.celsius(monitor.gpuHotspotTemp) },
                { "key": "VRAM", "value": Format.celsius(monitor.gpuVramTemp) }
            ]
        },
        PartRule {
            width: parent.width
        },
        StatRow {
            width: parent.width
            stats: [
                { "key": "Fan", "value": Format.rpm(monitor.gpuFan) },
                { "key": "Power draw", "value": Format.power(monitor.gpuPower, monitor.gpuPowerCap) }
            ]
        }
    ]
}
