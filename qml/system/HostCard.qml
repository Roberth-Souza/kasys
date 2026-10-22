import QtQuick
import ".."

// OS and kernel on the left, boot setup on the right. The OS is read once per
// opening, the rest at startup.
PairCard {
    title: "Host information"
    glyph: Config.glyphHost

    leftRows: [
        { "label": "OS", "value": Format.text(monitor.osName) },
        { "label": "Kernel", "value": Format.text(monitor.kernel) },
        { "label": "Architecture", "value": Format.text(monitor.architecture) },
        { "label": "Packages", "value": monitor.packages < 0 ? Format.missing : monitor.packages + " (pacman)" }
    ]
    rightRows: [
        { "label": "Boot mode", "value": Format.flag(monitor.uefi, "UEFI", "BIOS") },
        { "label": "Secure Boot", "value": Format.flag(monitor.secureBoot, "Enabled", "Disabled") },
        { "label": "Bootloader", "value": Format.text(monitor.bootloader) }
    ]
}
