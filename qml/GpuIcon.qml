import QtQuick
import QtQuick.Shapes
import "."

// A graphics card drawn by hand, since no Nerd Font glyph has fans: the
// shroud with two fans. Drawn on an 18x11 pixel grid (1px lines on .5 so
// they land on whole pixels) and scaled to `width`; takes `color` like a
// Label.
Item {
    id: root

    property color color: Config.fg

    implicitWidth: Config.gpuIconWidth
    implicitHeight: Config.gpuIconWidth * 11 / 18

    Shape {
        width: 18
        height: 11
        scale: root.width / 18
        transformOrigin: Item.TopLeft
        preferredRendererType: Shape.CurveRenderer

        // Shroud.
        ShapePath {
            strokeColor: root.color
            strokeWidth: 1
            fillColor: "transparent"

            PathSvg { path: "M0.5 0.5 L17.5 0.5 L17.5 10.5 L0.5 10.5 Z" }
        }

        // Fan rings.
        ShapePath {
            strokeColor: root.color
            strokeWidth: 1
            fillColor: "transparent"

            PathSvg { path: "M2 5.5 A3 3 0 1 0 8 5.5 A3 3 0 1 0 2 5.5 Z" }
            PathSvg { path: "M10 5.5 A3 3 0 1 0 16 5.5 A3 3 0 1 0 10 5.5 Z" }
        }

        // Fan hubs.
        ShapePath {
            strokeColor: "transparent"
            fillColor: root.color

            PathSvg { path: "M4.2 5.5 A0.8 0.8 0 1 0 5.8 5.5 A0.8 0.8 0 1 0 4.2 5.5 Z" }
            PathSvg { path: "M12.2 5.5 A0.8 0.8 0 1 0 13.8 5.5 A0.8 0.8 0 1 0 12.2 5.5 Z" }
        }
    }
}
