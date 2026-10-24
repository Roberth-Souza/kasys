import QtQuick
import ".."

// The Hardware tab: one row per physical part, drawing | identity | live,
// then Motherboard | Display side by side taking what is left. A value with
// no collector yet says so; it never shows made-up numbers.
Column {
    id: root

    readonly property int splitHeight: height - Config.hwCpuHeight - Config.hwGpuHeight
                                       - Config.hwMemoryHeight - Config.hwStorageHeight
                                       - 4 * Config.blockGap

    spacing: Config.blockGap

    ProcessorRow {
        width: Config.pageWidth
        height: Config.hwCpuHeight
    }

    GraphicsRow {
        width: Config.pageWidth
        height: Config.hwGpuHeight
    }

    MemoryRow {
        width: Config.pageWidth
        height: Config.hwMemoryHeight
    }

    StorageRow {
        width: Config.pageWidth
        height: Config.hwStorageHeight
    }

    Row {
        spacing: Config.blockGap

        MotherboardCard {
            width: Config.halfWidth
            height: root.splitHeight
        }

        DisplayCard {
            width: Config.halfWidth
            height: root.splitHeight
        }
    }
}
