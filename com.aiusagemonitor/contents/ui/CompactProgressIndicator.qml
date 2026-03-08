import QtQuick

Item {
    id: root

    property var tokens: null
    property real pct: 0
    property color toneColor: "transparent"
    property string displayText: "-"
    property bool showText: true

    width: 34
    height: 34

    Canvas {
        id: progressCanvas
        anchors.fill: parent

        onPaint: {
            var ctx = getContext("2d")
            ctx.clearRect(0, 0, width, height)
            var cx = width / 2
            var cy = height / 2
            var r = cx - 3
            var lw = 3

            ctx.beginPath()
            ctx.arc(cx, cy, r, 0, 2 * Math.PI)
            if (root.tokens) {
                ctx.strokeStyle = Qt.rgba(
                    root.tokens.separator.r,
                    root.tokens.separator.g,
                    root.tokens.separator.b,
                    0.85
                )
            } else {
                ctx.strokeStyle = "rgba(140, 140, 140, 0.85)"
            }
            ctx.lineWidth = lw
            ctx.stroke()

            if (root.pct > 0) {
                ctx.beginPath()
                ctx.arc(
                    cx,
                    cy,
                    r,
                    -Math.PI / 2,
                    -Math.PI / 2 + 2 * Math.PI * (root.pct / 100)
                )
                ctx.strokeStyle = root.toneColor
                ctx.lineWidth = lw
                ctx.stroke()
            }
        }

        onWidthChanged: requestPaint()
        onHeightChanged: requestPaint()
    }

    onPctChanged: progressCanvas.requestPaint()
    onToneColorChanged: progressCanvas.requestPaint()

    Text {
        visible: root.showText
        anchors.centerIn: parent
        text: root.displayText
        font.pixelSize: 9
        font.bold: true
        color: root.toneColor
        horizontalAlignment: Text.AlignHCenter
    }
}
