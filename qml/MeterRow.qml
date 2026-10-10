import QtQuick
import "."

// label | value | detail | bar. The columns are fixed so the bars of the
// rows in one card start at the same x.
Item {
    id: root

    property string label: ""
    property color labelColor: Config.fg
    property string value: Format.missing
    property string detail: ""
    property real fraction: -1
    property color valueColor: Config.fgActive
    property int labelWidth: Config.meterLabelWidth
    property int valueWidth: Config.meterValueWidth
    property int detailWidth: 0

    height: Config.meterRowHeight

    Label {
        id: labelText

        anchors.verticalCenter: parent.verticalCenter
        width: root.labelWidth
        text: root.label
        color: root.labelColor
    }

    Label {
        id: valueText

        anchors.verticalCenter: parent.verticalCenter
        anchors.left: labelText.right
        width: root.valueWidth
        text: root.value
        color: root.value === Format.missing ? Config.fgDim : root.valueColor
    }

    Label {
        id: detailText

        anchors.verticalCenter: parent.verticalCenter
        anchors.left: valueText.right
        width: root.detailWidth
        visible: root.detailWidth > 0
        text: root.detail
        color: Config.fgDim
        font.pixelSize: Config.fontSizeSmall
    }

    Bar {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: root.detailWidth > 0 ? detailText.right : valueText.right
        anchors.right: parent.right
        fraction: root.fraction
    }
}
