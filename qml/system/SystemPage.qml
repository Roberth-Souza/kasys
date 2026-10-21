import QtQuick
import ".."

// The System tab: page title, UPTIME | BOOT TIME | OS AGE, then Boot analysis
// | Host information and Startup services | Desktop & session. A card with
// no collector yet says so; it never shows made-up numbers.
Column {
    id: root

    readonly property int middleHeight: height - Config.pageHeaderHeight - Config.statCardHeight
                                        - Config.sessionCardHeight - 3 * Config.blockGap

    spacing: Config.blockGap

    // Indented to line up with the text inside the cards.
    Column {
        x: Config.cardPad
        width: parent.width - x
        height: Config.pageHeaderHeight

        Label {
            width: parent.width
            height: Config.pageTitleHeight
            verticalAlignment: Text.AlignVCenter
            text: "System"
            color: Config.fgActive
            font.pixelSize: Config.fontSizeLarge
        }

        Label {
            width: parent.width
            height: Config.pageSubtitleHeight
            text: "Host, boot and session information"
            color: Config.fgDim
        }
    }

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

        PendingCard {
            width: Config.columnWidth
            height: Config.statCardHeight
            title: "BOOT TIME"
            glyph: Config.glyphBootTime
        }

        StatCard {
            width: Config.columnWidth
            height: Config.statCardHeight
            title: "OS AGE"
            glyph: Config.glyphOsAge
            value: Format.days(monitor.osAgeDays)
            detail: monitor.installDate < 0 ? "" : "Installed " + Format.date(monitor.installDate)
        }
    }

    Row {
        spacing: Config.blockGap

        PendingCard {
            width: Config.wideColumnWidth
            height: root.middleHeight
            title: "Boot analysis"
            glyph: Config.glyphBoot
        }

        HostCard {
            width: Config.columnWidth
            height: root.middleHeight
        }
    }

    Row {
        spacing: Config.blockGap

        PendingCard {
            width: Config.wideColumnWidth
            height: Config.sessionCardHeight
            title: "Startup services"
            glyph: Config.glyphServices
        }

        SessionCard {
            width: Config.columnWidth
            height: Config.sessionCardHeight
        }
    }
}
