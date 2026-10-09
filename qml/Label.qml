import QtQuick
import "."

// Text with the app's font: every line of text in the window is one of these.
Text {
    color: Config.fg
    textFormat: Text.PlainText
    elide: Text.ElideRight
    font.family: Config.font
    font.pixelSize: Config.fontSize
}
