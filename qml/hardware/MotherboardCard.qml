import QtQuick
import ".."
import "art.js" as Art

// Board and vendor, BIOS and boot mode. Boot mode is the host's (`uefi`),
// not the board's.
PartCard {
    readonly property var bios: [monitor.biosVersion, Format.isoDate(monitor.biosDate)]
        .filter(part => part !== "" && part !== Format.missing)

    art: Art.board()
    artWidth: Config.artBoardWidth

    PartTitle {
        width: parent.width
        title: "Motherboard"
        name: Format.text(monitor.boardName)
        detail: Format.text(monitor.boardVendor)
    }

    PartRule {
        width: parent.width
    }

    PartPairs {
        width: parent.width
        rows: [
            { "label": "BIOS", "value": bios.length ? bios.join(" · ") : Format.missing },
            { "label": "Boot mode", "value": Format.flag(monitor.uefi, "UEFI", "BIOS") }
        ]
    }
}
