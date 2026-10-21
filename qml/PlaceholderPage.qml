import QtQuick
import "."

// A sidebar page that has no content yet.
Card {
    property string name: ""
    property string pageGlyph: ""

    title: name
    glyph: pageGlyph

    Label {
        anchors.centerIn: parent
        text: Format.notBuilt
        color: Config.fgDim
    }
}
