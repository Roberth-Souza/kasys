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
        text: "Not built yet"
        color: Config.fgDim
    }
}
