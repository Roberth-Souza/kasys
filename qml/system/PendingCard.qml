import QtQuick
import ".."

// A card whose collector is not written yet: title and glyph only.
Card {
    Label {
        anchors.centerIn: parent
        text: Format.notBuilt
        color: Config.fgDim
    }
}
