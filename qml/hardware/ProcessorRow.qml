import QtQuick
import ".."
import "art.js" as Art

// Model, core counts, clock driver and power profile beside the chip, the
// package temperature and highest clock live.
PartRow {
    id: root

    // "AMD Ryzen 5 5600X" -> "AMD" over "RYZEN 5" on the chip: the brand,
    // then the rest without the model number. Intel puts the tier inside
    // the model number, so the part before a "-" stays: "Intel Core
    // i7-12700K" -> "INTEL" over "CORE I7". Intel untested: no machine.
    readonly property var words: monitor.cpuModel.split(" ").filter(word => word !== "")
    readonly property var series: {
        const kept = root.words.slice(1, Math.max(2, root.words.length - 1));
        const last = root.words[root.words.length - 1] ?? "";
        const tier = last.split("-")[0];
        // Only when the model number was dropped, not kept as the series.
        if (root.words.length > 2 && last.includes("-") && tier !== "")
            kept.push(tier);
        return kept;
    }

    art: Art.cpu((root.words[0] ?? "").toUpperCase(), root.series.join(" ").toUpperCase())
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
