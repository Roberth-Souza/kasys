import QtQuick
import ".."

// Last startup split into systemd's phases (firmware, loader, kernel, initrd,
// userspace; whichever this machine has): the total on the left, one column
// per phase with its share, the phase bar under them and the longest phase.
Card {
    id: root

    readonly property var phases: monitor.bootPhases
    readonly property real total: monitor.bootTotal
    // The phases can add up a few ms past the total: scale the bar to the larger.
    readonly property real span: Math.max(total, phases.reduce((sum, p) => sum + p.seconds, 0))
    readonly property var longest: phases.reduce((best, p) => best === null || p.seconds > best.seconds ? p : best, null)

    function phaseColor(index) { return Config.bootPhaseColors[index % Config.bootPhaseColors.length]; }

    function phaseGlyph(name) { return Config.glyphPhases[name] ?? Config.glyphPhaseOther; }

    function share(seconds) { return root.total > 0 ? Format.percent(100 * seconds / root.total) : Format.missing; }

    function startOf(index) {
        let start = 0;
        for (let i = 0; i < index; i++)
            start += phases[i].seconds;
        return start;
    }

    component Rule: Rectangle {
        anchors.left: parent.left
        anchors.right: parent.right
        height: 1
        color: Config.border
    }

    component Divider: Rectangle {
        width: 1
        color: Config.border
    }

    // -- total | phase columns + bar -----------------------------------------
    Item {
        id: lastStartup

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: Config.bootStartupHeight

        Column {
            width: Config.bootTotalWidth
            anchors.verticalCenter: parent.verticalCenter
            spacing: Config.statGap

            Label {
                width: parent.width
                text: "TOTAL BOOT TIME"
            }

            Label {
                width: parent.width
                height: Config.bigValueHeight
                verticalAlignment: Text.AlignVCenter
                text: Format.seconds(root.total)
                color: root.total < 0 ? Config.fgDim : Config.fgActive
                font.pixelSize: Config.fontSizeHuge
            }
        }

        Item {
            id: phaseArea

            anchors.left: parent.left
            anchors.leftMargin: Config.bootTotalWidth
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            Divider {
                anchors.top: parent.top
                anchors.bottom: parent.bottom
            }

            Label {
                visible: root.phases.length === 0
                anchors.centerIn: parent
                text: Format.missing
                color: Config.fgDim
            }

            Row {
                id: columns

                width: parent.width
                height: Config.bootPhasesHeight

                Repeater {
                    model: root.phases

                    Item {
                        required property var modelData
                        required property int index

                        width: columns.width / root.phases.length
                        height: parent.height

                        // The first column's divider is the one beside the total.
                        Divider {
                            visible: index > 0
                            height: parent.height
                        }

                        Column {
                            x: Config.bootColumnPad
                            width: parent.width - Config.bootColumnPad
                            spacing: Config.statGap

                            Label {
                                height: Config.bootPhaseIconHeight
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideNone
                                text: root.phaseGlyph(modelData.name)
                                color: Config.fgActive
                                font.pixelSize: Config.bootPhaseIconSize
                            }

                            Label {
                                width: parent.width
                                height: Config.bootPhaseNameHeight
                                text: Format.capitalize(modelData.name)
                            }

                            Label {
                                width: parent.width
                                height: Config.bootPhaseValueHeight
                                verticalAlignment: Text.AlignVCenter
                                text: Format.seconds(modelData.seconds)
                                color: Config.fgActive
                                font.pixelSize: Config.bootPhaseValueSize
                            }

                            Label {
                                width: parent.width
                                height: Config.bootPhasePercentHeight
                                text: root.share(modelData.seconds)
                                color: Config.fgDim
                            }
                        }
                    }
                }
            }

            Rectangle {
                id: bar

                anchors.top: columns.bottom
                anchors.topMargin: Config.bootBarGap
                anchors.left: parent.left
                anchors.leftMargin: Config.bootColumnPad
                anchors.right: parent.right
                height: Config.bootBarHeight
                color: Config.barTrack

                Repeater {
                    model: root.span > 0 ? root.phases : []

                    Rectangle {
                        required property var modelData
                        required property int index

                        readonly property real startX: Math.round(bar.width * root.startOf(index) / root.span)
                        readonly property real endX: Math.round(bar.width * (root.startOf(index) + modelData.seconds) / root.span)

                        x: startX
                        width: Math.max(1, endX - startX - (index < root.phases.length - 1 ? Config.bootSegmentGap : 0))
                        height: parent.height
                        color: root.phaseColor(index)
                    }
                }
            }

            Label {
                anchors.top: bar.bottom
                anchors.topMargin: Config.statGap
                anchors.left: bar.left
                height: Config.bootAxisHeight
                visible: root.span > 0
                text: "0 s"
                color: Config.fgDim
            }

            Label {
                anchors.top: bar.bottom
                anchors.topMargin: Config.statGap
                anchors.right: bar.right
                height: Config.bootAxisHeight
                visible: root.span > 0
                text: Format.seconds(root.total)
                color: Config.fgDim
            }
        }
    }

    // -- longest phase -------------------------------------------------------
    Rule {
        id: longestRule

        anchors.top: lastStartup.bottom
        anchors.topMargin: Config.ruleGap
    }

    Item {
        id: longestRow

        anchors.top: longestRule.bottom
        anchors.topMargin: Config.ruleGap
        anchors.left: parent.left
        anchors.right: parent.right
        height: Config.bootLongestHeight

        Row {
            id: longestKey

            height: parent.height
            spacing: Config.gap

            Label {
                width: Config.iconWidth
                height: parent.height
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideNone
                text: Config.glyphLongest
                font.pixelSize: Config.iconSize
            }

            Label {
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideNone
                text: "Longest stage"
                color: Config.fgDim
            }

            Divider {
                anchors.verticalCenter: parent.verticalCenter
                height: Config.bootLongestRuleHeight
            }

            Label {
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideNone
                text: root.longest ? Format.capitalize(root.longest.name) : Format.missing
                color: root.longest ? Config.fgActive : Config.fgDim
            }
        }

        Label {
            anchors.left: longestKey.right
            anchors.leftMargin: Config.gap
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            horizontalAlignment: Text.AlignRight
            visible: root.longest !== null
            text: root.longest ? Format.seconds(root.longest.seconds) + " · " + root.share(root.longest.seconds) : ""
            color: Config.fgActive
        }
    }
}
