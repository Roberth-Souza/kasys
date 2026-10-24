import QtQuick
import ".."
import "art.js" as Art

// Model and core counts beside the chip, the package temperature live.
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
            { "key": "L3 cache", "value": Format.notBuilt }
        ]
    }

    live: Stat {
        width: parent.width
        key: "CPU temperature"
        value: Format.celsius(monitor.cpuTemp)
        valueSize: Config.fontSizeHuge
        valueHeight: Config.bigValueHeight
    }
}
