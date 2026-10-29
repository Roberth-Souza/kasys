.pragma library

// The text of "Copy hardware specs": identity only (no temperatures, clocks
// or usage), plain text with aligned labels, for a forum post or an issue.
// A value that is unknown is left out; a line with nothing left is dropped.

const LABEL_WIDTH = "Motherboard: ".length;

// Parts that are known, joined: "" and Format.missing are left out.
function known(parts, separator, format) {
    return parts.filter(part => part !== "" && part !== format.missing).join(separator);
}

function count(n, word) {
    return n + " " + word + (n === 1 ? "" : "s");
}

// "Motherboard: ..." with every line after the first under the first value.
function block(label, lines) {
    const kept = lines.filter(line => line !== "");
    if (!kept.length)
        return [];
    const indent = " ".repeat(LABEL_WIDTH);
    return kept.map((line, i) => (i === 0 ? (label + ":").padEnd(LABEL_WIDTH) : indent) + line);
}

function cpu(monitor, format) {
    const counts = monitor.cpuCores < 0 || monitor.cpuThreads < 0 ? ""
        : "(" + count(monitor.cpuCores, "core") + " / " + count(monitor.cpuThreads, "thread") + ")";
    return known([monitor.cpuModel, counts], " ", format);
}

function gpu(monitor, format) {
    const mesa = monitor.mesaVersion === "" ? "" : "Mesa " + monitor.mesaVersion;
    return known([monitor.gpuName, monitor.gpuDriver, mesa], ", ", format);
}

// "32 GiB DDR4 3200 MT/s, dual channel": the channel count is always said,
// single channel is the one worth seeing.
function memory(monitor, format) {
    const size = monitor.memoryInstalled < 0 ? "" : format.bytes(monitor.memoryInstalled);
    const head = known([size, monitor.memoryType, format.mts(monitor.memorySpeed)], " ", format);
    const channels = format.channels(monitor.memoryChannels);
    return known([head, channels === format.missing ? "" : channels.toLowerCase()], ", ", format);
}

// What SMART checked, not a verdict: "no warnings, 0 media errors, 6% used"
// (NVMe) or "not failing, 0 bad sectors" (ATA). "" when SMART was not read.
function smart(disk, format) {
    if (!disk.smart)
        return "";
    const nvme = disk.kind === "NVMe";
    let alarm = "";
    if (disk.smartAlarm === 0)
        alarm = nvme ? "no warnings" : "not failing";
    else if (disk.smartAlarm > 0)
        alarm = nvme ? "warnings: " + disk.smartWarnings : "failing";
    const errors = disk.smartErrors < 0 ? "" : count(disk.smartErrors, nvme ? "media error" : "bad sector");
    const wear = nvme && disk.lifespanUsed >= 0 ? format.percent(disk.lifespanUsed) + " used" : "";
    const checked = known([alarm, errors, wear], ", ", format);
    return checked === "" ? "" : "SMART: " + checked;
}

// Every disk, mounted or not: model, size and kind, filesystem; SMART under it.
function storage(disks, format) {
    const lines = [];
    for (const disk of disks) {
        const size = known([disk.size < 0 ? "" : format.bytes(disk.size), disk.kind], " ", format);
        lines.push(known([disk.model === "" ? disk.name : disk.model, size, disk.fstype], ", ", format));
        lines.push(smart(disk, format));
    }
    return lines;
}

function board(monitor, format) {
    const date = format.isoDate(monitor.biosDate);
    const bios = monitor.biosVersion === "" ? known([date], "", format)
        : known([monitor.biosVersion, date === format.missing ? "" : "(" + date + ")"], " ", format);
    return known([known([monitor.boardVendor, monitor.boardName], " ", format),
                  bios === "" ? "" : "BIOS " + bios], ", ", format);
}

// `screen` comes from the Display card, the only place that has QML's Screen:
// { monitor: "AOC 2460G4 24\"", width, height (device pixels), hz, connector }.
function display(screen, format) {
    const mode = screen.width + "x" + screen.height + (screen.hz < 0 ? "" : " @ " + format.hz(screen.hz));
    return known([screen.monitor, mode, screen.connector], ", ", format);
}

function hardware(monitor, format, screen) {
    return [
        ...block("CPU", [cpu(monitor, format)]),
        ...block("GPU", [gpu(monitor, format)]),
        ...block("Memory", [memory(monitor, format)]),
        ...block("Storage", storage(monitor.storageDisks, format)),
        ...block("Motherboard", [board(monitor, format)]),
        ...block("Display", [display(screen, format)])
    ].join("\n");
}
