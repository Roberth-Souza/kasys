import QtQuick
import "."

// A thin horizontal meter. `fraction` runs 0..1; below 0 means no data and
// leaves the bare track.
Rectangle {
    id: root

    property real fraction: -1

    height: Config.barHeight
    color: Config.barTrack

    Rectangle {
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: root.fraction < 0 ? 0 : Math.round(root.width * Math.min(1, root.fraction))
        color: Config.barFill
    }
}
