pragma Singleton

import QtQuick

// Palette, font and geometry. Never hardcode a color or a size in a
// component; add a token here instead.
QtObject {
    // -- palette: greys only, same as gitframe ------------------------------
    readonly property color bg: "#f2000000"
    readonly property color cardBg: "#00000000"
    readonly property color fg: "#aaaaaa"
    readonly property color fgActive: "#ffffff"
    readonly property color fgDim: "#5d5d5d"
    readonly property color activeFill: "#9d9d9d"
    readonly property color fgInvert: "#000000"
    readonly property color border: "#3c3c3c"
    readonly property color clear: "#00000000"
    readonly property color menuBg: "#000000"
    readonly property color hoverFill: "#262626"

    // Graphs and bars. Opaque on purpose: the Canvas takes them as strings.
    readonly property color graphLine: "#d4d4d4"
    readonly property color graphLineSecond: "#6e6e6e"
    readonly property color graphFill: "#1c1c1c"
    readonly property color gridLine: "#2a2a2a"
    readonly property color gridLineFaint: "#161616"
    readonly property color barTrack: "#262626"
    readonly property color barFill: "#9d9d9d"

    // -- type ----------------------------------------------------------------
    readonly property string font: "JetBrainsMono Nerd Font"
    readonly property int fontSize: 12
    readonly property int fontSizeSmall: 11
    readonly property int fontSizeMedium: 14
    readonly property int fontSizeLarge: 26
    readonly property int fontSizeHuge: 40     // GPU utilization: "100%" still fits gpuUsageWidth
    readonly property int glyphSize: 14
    // Card heading and row icons. Sizes are matched by ink, not by number:
    // at 18 most glyphs draw about 14x15 px; the RAM stick is wide, so it
    // steps down.
    readonly property int iconSize: 18
    readonly property int iconSizeWide: 16
    readonly property int gpuIconWidth: 18    // GpuIcon, drawn instead of a glyph
    // Fixed icon cell, icon centred in it, so the text after it lines up.
    readonly property int iconWidth: 20

    // -- glyphs (Nerd Font, checked against the installed font) --------------
    readonly property string glyphApp: "\u{F0379}"          // md-monitor
    // CPU, RAM and GPU match caesar-shell's system popup.
    readonly property string glyphCpu: "\u{F035B}"          // md-memory (a chip)
    readonly property string glyphMemory: "\u{EFC5}"        // fa-memory (RAM stick)
    readonly property string glyphNetwork: "\u{F04E2}"      // md-swap_vertical
    readonly property string glyphGpu: "\u{F08AE}"         // md-expansion_card
    readonly property string glyphDisk: "\u{F02CA}"         // md-harddisk
    readonly property string glyphProcesses: "\u{F0279}"    // md-format_list_bulleted
    readonly property string glyphTemperature: "\u{F050F}"  // md-thermometer
    readonly property string glyphHardware: "\u{F01C5}"     // md-desktop_tower
    readonly property string glyphSystem: "\u{F02FD}"       // md-information_outline
    readonly property string glyphOverview: "\u{F0570}"     // md-view_grid
    readonly property string glyphAvatar: "\u{F0013}"       // md-account_outline
    readonly property string glyphDown: "\u{F01DA}"         // md-download
    readonly property string glyphUp: "\u{F0552}"           // md-upload
    readonly property string glyphChevronDown: "\u{F0140}"  // md-chevron_down
    // System page cards.
    readonly property string glyphUptime: "\u{F0150}"       // md-clock_outline
    readonly property string glyphLastUpdate: "\u{F06B0}"   // md-update
    readonly property string glyphOsAge: "\u{F00ED}"        // md-calendar
    readonly property string glyphHost: "\u{F048B}"         // md-server
    readonly property string glyphRecentBoots: "\u{F02DA}"  // md-history
    readonly property string glyphLongest: "\u{F053A}"      // md-trophy_outline
    // Boot phases by systemd-analyze's name; any other one (`soft reboot #1`)
    // gets glyphPhaseOther.
    readonly property var glyphPhases: ({
        "firmware": "\u{F4BC}",   // oct-cpu
        "loader": "\u{F09ED}",    // md-text_box_outline
        "kernel": "\u{F08BB}",    // md-cog_outline
        "initrd": "\u{F01A7}",    // md-cube_outline
        "userspace": "\u{F489}"   // oct-terminal
    })
    readonly property string glyphPhaseOther: "\u{F051B}"   // md-timer_outline
    readonly property string glyphServices: "\u{F08BB}"     // md-cog_outline
    readonly property string glyphSession: "\u{F0379}"      // md-monitor

    // -- geometry ------------------------------------------------------------
    readonly property int pad: 12           // window edge, same as the gap between cards
    readonly property int cardPad: 16       // inside a card
    readonly property int blockGap: 12      // between cards
    readonly property int gap: 8            // inside a card
    readonly property int sectionGap: 12    // graph to the rows under it
    readonly property int radius: 4
    readonly property int cardBorderWidth: 2
    readonly property int cardTitleHeight: 22
    readonly property int titleGap: 10      // card title to body
    readonly property int cardChrome: 2 * cardPad + cardTitleHeight + titleGap

    readonly property int sidebarWidth: 200
    readonly property int tabHeight: 40
    readonly property int sidebarRowPadX: 2 * gap
    // Tab glyphs: bigger than the card ones, in a fixed-width cell so the
    // labels line up whatever each glyph's own width.
    readonly property int sidebarGlyphSize: 22
    readonly property int sidebarGlyphWidth: 26
    readonly property int sidebarLabelSize: fontSizeMedium
    readonly property int ruleGap: 14

    // Three equal columns of cards beside the sidebar.
    readonly property int columnWidth: 380
    readonly property int columnInner: columnWidth - 2 * cardPad

    // Graphs: one minute of samples, with the axis labels left of the plot.
    readonly property int historyLength: 60
    readonly property int graphHeight: 64
    readonly property int cpuGraphHeight: 110
    readonly property int percentLabelWidth: 36
    readonly property int rateLabelWidth: 72
    readonly property int barHeight: 4

    readonly property int meterRowHeight: 22
    readonly property int meterLabelWidth: 96
    readonly property int meterValueWidth: 72
    readonly property int dropdownWidth: 120

    // CPU card: model + core counts, total / peak, top processes by CPU.
    readonly property int cpuModelHeight: 20
    readonly property int cpuCoresHeight: 18
    readonly property int cpuStatLabelHeight: 18
    readonly property int cpuStatHeight: 52
    readonly property int cpuTopRows: 3

    // GPU card: name, utilization + graph, VRAM bar, TEMP | CLOCK | FAN.
    readonly property int gpuNameHeight: 18
    readonly property int gpuUsageWidth: 110    // big % and its label, left of the graph
    readonly property int gpuGraphHeight: 80
    readonly property int gpuSpanHeight: 16     // "60s" under the graph
    readonly property int gpuVramBarHeight: 8
    readonly property int gpuStatHeight: 40

    readonly property int processRowHeight: 20
    readonly property int pidWidth: 64
    readonly property int processPercentWidth: 56
    readonly property int processMemWidth: 88
    readonly property int processTableTop: 6     // card title to the column labels
    readonly property int processHeaderGap: 6    // column labels to the first row

    readonly property int temperatureRowHeight: 26

    // System page, top to bottom: UPTIME | OS AGE | LAST UPDATE, Boot
    // analysis across the page, Recent boots | Startup services (taking
    // whatever height is left), then Host information | Desktop & session.
    readonly property int pageWidth: 3 * columnWidth + 2 * blockGap
    readonly property int halfWidth: (pageWidth - blockGap) / 2
    readonly property int bigValueHeight: 48     // one line at fontSizeHuge
    readonly property int statDetailHeight: 18
    readonly property int statCardHeight: cardChrome + bigValueHeight + statGap + statDetailHeight
    // Host information and Desktop & session: two label / value columns.
    readonly property int pairRowHeight: 22
    readonly property int pairLabelWidth: 120
    readonly property int pairRows: 4            // Host information's left column, the longest
    readonly property int pairCardHeight: cardChrome + pairRows * pairRowHeight

    // Boot analysis (no heading): total on the left, one column per phase
    // beside it with the phase bar under them, then the longest phase.
    // Phases are shaded dark to light in systemd's order (firmware first);
    // a sixth phase would reuse the first shade.
    readonly property var bootPhaseColors: ["#4a4a4a", "#6e6e6e", "#8c8c8c", "#adadad", "#d4d4d4"]
    readonly property int bootTotalWidth: 260
    readonly property int bootColumnPad: 12     // divider to the text of a phase column
    readonly property int bootPhaseIconSize: 22
    readonly property int bootPhaseIconHeight: 26
    readonly property int bootPhaseNameHeight: 18
    readonly property int bootPhaseValueSize: 22
    readonly property int bootPhaseValueHeight: 30
    readonly property int bootPhasePercentHeight: 16
    readonly property int bootPhasesHeight: bootPhaseIconHeight + bootPhaseNameHeight
                                            + bootPhaseValueHeight + bootPhasePercentHeight + 3 * statGap
    readonly property int bootBarHeight: 22
    readonly property int bootBarGap: 30        // phase columns to the bar
    readonly property int bootSegmentGap: 2     // black seam between two phases
    readonly property int bootAxisHeight: 16
    readonly property int bootLongestHeight: 22
    readonly property int bootLongestRuleHeight: 14
    readonly property int bootStartupHeight: bootPhasesHeight + bootBarGap + bootBarHeight
                                             + statGap + bootAxisHeight
    readonly property int bootCardHeight: 2 * cardPad + bootStartupHeight + 2 * ruleGap + 1
                                          + bootLongestHeight

    // Recent boots: total of each startup, the newest labelled on the right.
    readonly property var bootsScaleSteps: [5, 10, 20, 30, 40, 60, 90, 120]
    readonly property int bootsAxisWidth: 40      // "120 s"
    readonly property int bootsXAxisHeight: 18    // boot numbers under the plot
    readonly property var bootsGridDash: [2, 3]
    readonly property real bootsDotRadius: 2.5
    readonly property real bootsLastDotRadius: 4
    readonly property real bootsLastDotStroke: 1.5
    readonly property int bootsValuePad: 2        // black margin around a time label

    // Startup services: slowest units of the critical chain, bars scaled to
    // the slowest. The rows share whatever height the subtitle leaves.
    readonly property int servicesRows: 5
    readonly property int servicesSubtitleHeight: 18
    readonly property int servicesNameWidth: 240
    readonly property int servicesTimeWidth: 64
    readonly property int servicesBarHeight: 8

    // Hardware page: one card per part, split drawing | identity | live by
    // vertical rules, then Motherboard | Display side by side taking what is
    // left. Drawings are line art in one stroke weight whatever their size.
    readonly property color artLine: "#d4d4d4"
    readonly property real artStroke: 1.3
    readonly property real artThinStroke: 0.8
    readonly property real artThinOpacity: 0.7
    readonly property int artCpuWidth: 100
    readonly property int artGpuWidth: 252
    readonly property int artRamWidth: 270
    readonly property int artNvmeWidth: 270
    readonly property int artBoardWidth: 112
    readonly property int artMonitorWidth: 130
    readonly property int partArtWidth: 290      // drawing column of a full-width row
    readonly property int partLiveWidth: 351     // live column, text width
    readonly property int partColumnGap: 24      // each side of a column rule
    readonly property int partSplitArtWidth: 150 // drawing column of a half card
    readonly property int partHeadHeight: 20
    readonly property int partNameHeight: 34
    readonly property int partSubHeight: 18
    readonly property int partRuleGap: 8         // above and below a rule
    readonly property int partKeyHeight: 16
    readonly property int partValueHeight: 20
    readonly property int partMidHeight: 32      // one line at fontSizeLarge
    readonly property int partStatGap: 16        // each side of a stat rule
    readonly property int partBarHeight: 6
    readonly property int partBarGap: 6
    readonly property int partSlotHeight: 20
    readonly property int partSlotGap: 12
    readonly property int partPairLabelWidth: 90
    readonly property int hwCpuHeight: 136
    readonly property int hwGpuHeight: 163       // fits the identity column with the Interface note
    readonly property int hwGpuBottomPad: 6      // the note sits close to the bottom border
    readonly property int hwMemoryHeight: 128
    readonly property int hwStorageHeight: 150
    readonly property int memorySlots: 4         // drawn until the memory collector says how many

    // System card: the avatar takes whatever height the text leaves.
    readonly property int avatarGlyphSize: 64
    readonly property int statGap: 4        // small label to its big value
    readonly property int shellRowHeight: 22

    // Fixed card heights; the last card of each column takes what is left.
    // Header row + cpuTopRows rows under TOP BY CPU (bridge: TOP_CPU_PROCESSES).
    readonly property int cpuCardHeight: cardChrome + cpuGraphHeight + 3 * sectionGap
                                         + cpuModelHeight + cpuCoresHeight + cpuStatHeight
                                         + (1 + cpuTopRows) * processRowHeight
    readonly property int memoryCardHeight: cardChrome + graphHeight + sectionGap
                                            + 2 * meterRowHeight
    readonly property int gpuCardHeight: cardChrome + 4 * sectionGap + gpuNameHeight
                                         + gpuGraphHeight + gpuSpanHeight
                                         + meterRowHeight + gap + gpuVramBarHeight
                                         + 1 + gpuStatHeight
    // Plus one meterRowHeight per disk row: see Overview.
    readonly property int diskCardBaseHeight: cardChrome + graphHeight + sectionGap
    // Plus one temperatureRowHeight per chip: see Overview.
    readonly property int temperatureCardBaseHeight: cardChrome

    readonly property int windowWidth: 2 * pad + sidebarWidth + blockGap
                                       + 3 * columnWidth + 2 * blockGap
    readonly property int windowHeight: 800
    readonly property int contentHeight: windowHeight - 2 * pad

    // -- animation -----------------------------------------------------------
    readonly property int animFast: 80
}
