import QtQuick
import ".."

// OS, kernel and boot setup. Everything but the OS is read once at startup.
Card {
    title: "Host information"
    glyph: Config.glyphHost

    Column {
        anchors.left: parent.left
        anchors.right: parent.right

        InfoRow {
            width: parent.width
            height: Config.hostRowHeight
            label: "OS"
            value: Format.text(monitor.osName)
        }

        InfoRow {
            width: parent.width
            height: Config.hostRowHeight
            label: "Kernel"
            value: Format.text(monitor.kernel)
        }

        InfoRow {
            width: parent.width
            height: Config.hostRowHeight
            label: "Architecture"
            value: Format.text(monitor.architecture)
        }

        InfoRow {
            width: parent.width
            height: Config.hostRowHeight
            label: "Boot mode"
            value: Format.flag(monitor.uefi, "UEFI", "BIOS")
        }

        InfoRow {
            width: parent.width
            height: Config.hostRowHeight
            label: "Secure Boot"
            value: Format.flag(monitor.secureBoot, "Enabled", "Disabled")
        }

        InfoRow {
            width: parent.width
            height: Config.hostRowHeight
            label: "Bootloader"
            value: Format.text(monitor.bootloader)
        }

        InfoRow {
            width: parent.width
            height: Config.hostRowHeight
            label: "Packages"
            value: monitor.packages < 0 ? Format.missing : monitor.packages + " (pacman)"
        }
    }
}
