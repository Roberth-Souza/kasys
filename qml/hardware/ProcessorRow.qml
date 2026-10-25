import QtQuick
import ".."
import "art.js" as Art

// Model, core counts, clock driver and power profile beside the chip, the
// package temperature and highest clock live.
PartRow {
    id: root

    // "AMD Ryzen 5 5600X" -> "AMD" over "RYZEN 5" on the chip: the brand,
    // then the rest without the model number.
    readonly property var words: monitor.cpuModel.split(" ").filter(word => word !== "")

    art: Art.cpu((root.words[0] ?? "").toUpperCase(),
                 root.words.slice(1, Math.max(2, root.words.length - 1)).join(" ").toUpperCase())
    artWidth: Config.artCpuWidth

    PartTitle {
        width: parent.width
        title: "Processor"
        name: Format.text(monitor.cpuModel)
        hasDetail: false
    }

    PartRule {
        width: parent.width
    }

    StatRow {
        width: parent.width
        stats: [
            {
                "key": "Cores / threads",
                "value": monitor.cpuCores < 0 || monitor.cpuThreads < 0
                         ? Format.missing : monitor.cpuCores + " / " + monitor.cpuThreads
            },
            { "key": "Clock driver", "value": Format.text(monitor.cpuDriver) },
            { "key": "Power profile", "value": Format.powerProfile(monitor.cpuGovernor, monitor.cpuEpp) }
        ]
    }

    live: StatRow {
        width: parent.width
        valueSize: Config.fontSizeHuge
        valueHeight: Config.bigValueHeight
        stats: [
            { "key": "CPU temperature", "value": Format.celsius(monitor.cpuTemp) },
            { "key": "Clock", "value": Format.ghz(monitor.cpuFreq) }
        ]
    }
}
