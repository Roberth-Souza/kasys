import QtQuick
import ".."

// The System tab: UPTIME | OS AGE | LAST UPDATE, Boot analysis across the
// page, Recent boots | Startup services, then Host information | Desktop &
// session. A card with no collector yet says so; it never shows made-up
// numbers.
Column {
    id: root

    readonly property int middleHeight: height - Config.statCardHeight - Config.bootCardHeight
                                        - Config.pairCardHeight - 3 * Config.blockGap

    spacing: Config.blockGap

    Row {
        spacing: Config.blockGap

        StatCard {
            width: Config.columnWidth
            height: Config.statCardHeight
            title: "UPTIME"
            glyph: Config.glyphUptime
            value: Format.uptime(monitor.uptime)
            detail: monitor.uptime < 0 ? "" : "Since " + Format.bootClock(monitor.uptime)
        }

        StatCard {
            width: Config.columnWidth
            height: Config.statCardHeight
            title: "OS AGE"
            glyph: Config.glyphOsAge
            value: Format.days(monitor.osAgeDays)
            detail: monitor.installDate < 0 ? "" : "Installed " + Format.date(monitor.installDate)
        }

        PendingCard {
            width: Config.columnWidth
            height: Config.statCardHeight
            title: "LAST UPDATE"
            glyph: Config.glyphLastUpdate
        }
    }

    BootCard {
        width: Config.pageWidth
        height: Config.bootCardHeight
    }

    Row {
        spacing: Config.blockGap

        PendingCard {
            width: Config.halfWidth
            height: root.middleHeight
            title: "Recent boots"
            glyph: Config.glyphRecentBoots
        }

        PendingCard {
            width: Config.halfWidth
            height: root.middleHeight
            title: "Startup services"
            glyph: Config.glyphServices
        }
    }

    Row {
        spacing: Config.blockGap

        HostCard {
            width: Config.halfWidth
            height: Config.pairCardHeight
        }

        SessionCard {
            width: Config.halfWidth
            height: Config.pairCardHeight
        }
    }
}
