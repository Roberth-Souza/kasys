pragma Singleton

import QtQuick

// Display formatting. Every reading reaches QML raw (bytes, kHz, seconds);
// a negative one means its collector failed and is drawn as `missing`.
QtObject {
    readonly property string missing: "--"
    // What a card or row without a collector yet shows instead of a value.
    readonly property string notBuilt: "Not built yet"
    // Dates follow the English labels, whatever the system locale.
    readonly property var dateLocale: Qt.locale("en_US")
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

    function mhz(hz) { return hz < 0 ? missing : Math.round(hz / 1e6) + " MHz"; }

    function celsius(v) { return v < 0 ? missing : Math.round(v) + "°C"; }

    function rpm(n) { return n < 0 ? missing : n + " RPM"; }

    // µW; the cap is left out when unknown.
    function power(uW, capUW) {
        if (uW < 0)
            return missing;
        const watts = Math.round(uW / 1e6) + " W";
        return capUW < 0 ? watts : watts + " of " + Math.round(capUW / 1e6) + " W";
    }

    function ghz(kHz) { return kHz < 0 ? missing : (kHz / 1e6).toFixed(2) + " GHz"; }

    // "3d 4h", "2h 34m" or "34m": short enough for the big System card digits.
    function uptime(seconds) {
        if (seconds < 0)
            return missing;
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor(seconds % 86400 / 3600);
        const minutes = Math.floor(seconds % 3600 / 60);
        if (days > 0)
            return days + "d " + hours + "h";
        if (hours > 0)
            return hours + "h " + minutes + "m";
        return minutes + "m";
    }

    // "2d ago", "3h ago", "12m ago"; under a minute is "Just now".
    function ago(seconds) {
        if (seconds < 0)
            return missing;
        if (seconds >= 86400)
            return Math.floor(seconds / 86400) + "d ago";
        if (seconds >= 3600)
            return Math.floor(seconds / 3600) + "h ago";
        if (seconds >= 60)
            return Math.floor(seconds / 60) + "m ago";
        return "Just now";
    }

    function days(n) { return n < 0 ? missing : n + (n === 1 ? " day" : " days"); }

    function text(s) { return s === "" ? missing : s; }

    // Raw collector value ("wayland" / "x11") to its display name.
    function displayServer(s) {
        if (s === "wayland")
            return "Wayland";
        if (s === "x11")
            return "X11";
        return text(s);
    }

    // A flag from the bridge: 1, 0, or negative when unknown.
    function flag(v, yes, no) { return v < 0 ? missing : (v ? yes : no); }

    // A boot time: "650 ms" under a second, "2.10 s" above.
    function seconds(v) {
        if (v < 0)
            return missing;
        return v < 1 ? Math.round(v * 1000) + " ms" : v.toFixed(2) + " s";
    }

    function capitalize(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

    function hz(v) { return v < 0 ? missing : Math.round(v) + " Hz"; }

    // "Apr 23, 2026" from milliseconds since the epoch.
    function date(ms) { return ms < 0 ? missing : new Date(ms).toLocaleString(dateLocale, "MMM d, yyyy"); }

    // "2026-04-17" from milliseconds since the epoch.
    function isoDate(ms) { return ms < 0 ? missing : new Date(ms).toLocaleString(dateLocale, "yyyy-MM-dd"); }

    // Display connector type from its DRM name: "DP-2" -> "DisplayPort",
    // "HDMI-A-1" -> "HDMI". An unknown type is shown raw.
    readonly property var connectorTypes: ({
        "DP": "DisplayPort",
        "eDP": "eDP",
        "HDMI-A": "HDMI",
        "HDMI-B": "HDMI",
        "DVI-I": "DVI",
        "DVI-D": "DVI",
        "DVI-A": "DVI",
        "VGA": "VGA",
        "LVDS": "LVDS"
    })

    function connector(name) {
        const type = name.replace(/-\d+$/, "");
        return connectorTypes[type] ?? text(type);
    }

    // A value that is drawn dim: failed, or its collector is not written yet.
    function absent(s) { return s === missing || s === notBuilt; }

    // When the machine came up, from the uptime: "07:42" if today,
    // "Oct 18, 07:42" before that.
    function bootClock(uptimeSeconds) {
        if (uptimeSeconds < 0)
            return missing;
        const boot = new Date(Date.now() - uptimeSeconds * 1000);
        const today = new Date().toDateString() === boot.toDateString();
        return boot.toLocaleString(dateLocale, today ? "HH:mm" : "MMM d, HH:mm");
    }

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
