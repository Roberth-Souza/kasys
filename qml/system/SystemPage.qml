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

        StatCard {
            width: Config.columnWidth
            height: Config.statCardHeight
            title: "LAST UPDATE"
            glyph: Config.glyphLastUpdate
            value: Format.ago(monitor.lastUpdateAge)
            detail: monitor.lastUpdate < 0 ? "" : Format.date(monitor.lastUpdate)
        }
    }

    BootCard {
        width: Config.pageWidth
        height: Config.bootCardHeight
    }

    Row {
        spacing: Config.blockGap

        RecentBootsCard {
            width: Config.halfWidth
            height: root.middleHeight
        }

        StartupServicesCard {
            width: Config.halfWidth
            height: root.middleHeight
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
