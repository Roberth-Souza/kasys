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
    readonly property int glyphSize: 14

    // -- glyphs (Nerd Font, checked against the installed font) --------------
    readonly property string glyphApp: "\u{F0379}"          // md-monitor
    readonly property string glyphCpu: ""             // oct-cpu
    readonly property string glyphMemory: "\u{F035B}"       // md-memory
    readonly property string glyphNetwork: "\u{F04E2}"      // md-swap_vertical
    readonly property string glyphGpu: "\u{F08AE}"         // md-expansion_card
    readonly property string glyphDisk: "\u{F02CA}"         // md-harddisk
    readonly property string glyphProcesses: "\u{F0279}"    // md-format_list_bulleted
    readonly property string glyphTemperature: "\u{F050F}"  // md-thermometer
    readonly property string glyphChip: "\u{F061A}"         // md-chip
    readonly property string glyphSystem: "\u{F02FD}"       // md-information_outline
    readonly property string glyphOverview: "\u{F056E}"     // md-view_dashboard
    readonly property string glyphAvatar: "\u{F0013}"       // md-account_outline
    readonly property string glyphDown: "\u{F01DA}"         // md-download
    readonly property string glyphUp: "\u{F0552}"           // md-upload

    // -- geometry ------------------------------------------------------------
    readonly property int pad: 12           // window edge, same as the gap between cards
    readonly property int cardPad: 16       // inside a card
    readonly property int blockGap: 12      // between cards
    readonly property int gap: 8            // inside a card
    readonly property int sectionGap: 12    // graph to the rows under it
    readonly property int radius: 4
    readonly property int cardTitleHeight: 22
    readonly property int titleGap: 10      // card title to body
    readonly property int cardChrome: 2 * cardPad + cardTitleHeight + titleGap

    readonly property int sidebarWidth: 200
    readonly property int tabHeight: 26
    readonly property int sidebarRowPadX: 2 * gap
    // Tab glyphs: bigger than the card ones, in a fixed-width cell so the
    // labels line up whatever each glyph's own width.
    readonly property int sidebarGlyphSize: 18
    readonly property int sidebarGlyphWidth: 20
    readonly property int ruleGap: 14

    // Three equal columns of cards beside the sidebar.
    readonly property int columnWidth: 380
    readonly property int columnInner: columnWidth - 2 * cardPad

    // Graphs: one minute of samples, with the axis labels left of the plot.
    readonly property int historyLength: 60
    readonly property int graphHeight: 64
    readonly property int cpuGraphHeight: 90
    readonly property int percentLabelWidth: 36
    readonly property int rateLabelWidth: 72
    readonly property int barHeight: 4

    readonly property int meterRowHeight: 22
    readonly property int meterLabelWidth: 96
    readonly property int meterValueWidth: 72

    // Per-core rows: two columns, six rows covers 12 threads.
    readonly property int coreRows: 6
    readonly property int coreRowHeight: 18
    readonly property int coreColumnGap: 16
    readonly property int coreLabelWidth: 56
    readonly property int corePercentWidth: 36

    readonly property int gpuNameHeight: 18
    readonly property int gpuRows: 4
    readonly property int gpuRowHeight: 20

    readonly property int processRows: 12
    readonly property int processRowHeight: 20
    readonly property int pidWidth: 64
    readonly property int processPercentWidth: 56

    readonly property int temperatureRows: 5
    readonly property int temperatureRowHeight: 26

    readonly property int avatarWidth: 112
    readonly property int avatarHeight: 136
    readonly property int infoKeyWidth: 80
    readonly property int infoRowHeight: 24

    // Fixed card heights; the last card of each column takes what is left.
    readonly property int cpuCardHeight: cardChrome + cpuGraphHeight + sectionGap
                                         + coreRows * coreRowHeight
    readonly property int memoryCardHeight: cardChrome + graphHeight + sectionGap
                                            + 2 * meterRowHeight
    readonly property int gpuCardHeight: cardChrome + graphHeight + sectionGap
                                         + gpuNameHeight + gap
                                         + gpuRows * gpuRowHeight
    readonly property int diskCardHeight: cardChrome + graphHeight + sectionGap
                                          + meterRowHeight
    readonly property int temperatureCardHeight: cardChrome + temperatureRows
                                                 * temperatureRowHeight

    readonly property int windowWidth: 2 * pad + sidebarWidth + blockGap
                                       + 3 * columnWidth + 2 * blockGap
    readonly property int windowHeight: 800
    readonly property int contentHeight: windowHeight - 2 * pad

    // -- animation -----------------------------------------------------------
    readonly property int animFast: 80
}
