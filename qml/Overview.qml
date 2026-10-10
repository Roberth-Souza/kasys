import QtQuick
import "."

// Three columns of cards, laid out like the mockup. In each column the last
// card takes whatever height the fixed ones leave.
Row {
    id: root

    // Grows with the number of disks; Processes takes what is left.
    readonly property int diskCardHeight: Config.diskCardBaseHeight
                                          + Math.max(1, monitor.disks.length)
                                          * Config.meterRowHeight

    spacing: Config.blockGap

    Column {
        width: Config.columnWidth
        height: root.height
        spacing: Config.blockGap

        CpuPanel {
            width: parent.width
            height: Config.cpuCardHeight
        }

        MemoryPanel {
            width: parent.width
            height: Config.memoryCardHeight
        }

        NetworkPanel {
            width: parent.width
            height: root.height - Config.cpuCardHeight - Config.memoryCardHeight
                    - 2 * Config.blockGap
        }
    }

    Column {
        width: Config.columnWidth
        height: root.height
        spacing: Config.blockGap

        GpuPanel {
            width: parent.width
            height: Config.gpuCardHeight
        }

        DiskPanel {
            width: parent.width
            height: root.diskCardHeight
        }

        ProcessesPanel {
            width: parent.width
            height: root.height - Config.gpuCardHeight - root.diskCardHeight
                    - 2 * Config.blockGap
        }
    }

    Column {
        width: Config.columnWidth
        height: root.height
        spacing: Config.blockGap

        TemperaturePanel {
            width: parent.width
            height: Config.temperatureCardHeight
        }

        SystemPanel {
            width: parent.width
            height: root.height - Config.temperatureCardHeight - Config.blockGap
        }
    }
}
