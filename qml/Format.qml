pragma Singleton

import QtQuick

// Display formatting. Every reading reaches QML raw (bytes, kHz, seconds);
// a negative one means its collector failed and is drawn as `missing`.
QtObject {
    readonly property string missing: "--"
    readonly property var byteUnits: ["B", "KiB", "MiB", "GiB", "TiB"]

    // 1 decimal under 100, none above; a trailing ".0" is dropped.
    function number(v) {
        const text = v < 100 ? v.toFixed(1) : Math.round(v).toString();
        return text.endsWith(".0") ? text.slice(0, -2) : text;
    }

    function bytes(n) {
        if (n < 0)
            return missing;
        let unit = 0;
        while (n >= 1024 && unit < byteUnits.length - 1) {
            n /= 1024;
            unit++;
        }
        return (unit === 0 ? Math.round(n).toString() : number(n)) + " " + byteUnits[unit];
    }

    function rate(n) { return n < 0 ? missing : bytes(n) + "/s"; }

    function percent(v) { return v < 0 ? missing : Math.round(v) + "%"; }

    // Used / total in the unit of the total, so both numbers line up:
    // "5.8" and " / 15.6 GiB", split so the used part can be drawn brighter.
    function usedOfTotal(used, total) {
        if (used < 0 || total < 0)
            return { "used": missing, "total": "" };
        let unit = 0;
        let scale = 1;
        while (total / scale >= 1024 && unit < byteUnits.length - 1) {
            scale *= 1024;
            unit++;
        }
        return {
            "used": number(used / scale),
            "total": " / " + number(total / scale) + " " + byteUnits[unit]
        };
    }

    function ghz(kHz) { return kHz < 0 ? missing : (kHz / 1e6).toFixed(2) + " GHz"; }

    // "2 days, 14:32", or "14:32" under a day.
    function uptime(seconds) {
        if (seconds < 0)
            return missing;
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor(seconds % 86400 / 3600);
        const minutes = Math.floor(seconds % 3600 / 60);
        const clock = hours + ":" + String(minutes).padStart(2, "0");
        if (days === 0)
            return clock;
        return days + (days === 1 ? " day, " : " days, ") + clock;
    }

    function text(s) { return s === "" ? missing : s; }

    // A round axis top for an auto-scaled graph: 1, 2 or 5 times a power of
    // ten, in B, KiB, MiB or GiB. Never below 1 KiB, so an idle link is flat.
    function niceMax(peak) {
        const steps = [1, 2, 5, 10, 20, 50, 100, 200, 500];
        for (let unit = 1024; unit <= Math.pow(1024, 3); unit *= 1024) {
            for (const step of steps) {
                if (step * unit >= peak)
                    return step * unit;
            }
        }
        return peak;
    }
}
