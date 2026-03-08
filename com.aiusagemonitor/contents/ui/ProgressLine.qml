import QtQuick
import QtQuick.Layouts

Item {
    id: root

    PopupTokens {
        id: tokens
    }

    property var percentValue: null
    property real thickness: tokens.progressThickness
    property real minFillWidth: 0
    property color trackColor: tokens.separator
    property color fillColor: tokens.accent
    property bool animated: true

    readonly property bool hasPercent: {
        if (percentValue === null || percentValue === undefined)
            return false
        return !isNaN(Number(percentValue))
    }
    readonly property real clampedPercent: hasPercent
        ? Math.max(0, Math.min(100, Number(percentValue)))
        : 0
    readonly property real computedFillWidth: {
        if (!hasPercent || clampedPercent <= 0)
            return 0
        var w = track.width * (clampedPercent / 100)
        if (minFillWidth > 0)
            w = Math.max(minFillWidth, w)
        return Math.min(track.width, w)
    }

    Layout.fillWidth: true
    implicitHeight: thickness

    Rectangle {
        id: track
        anchors.fill: parent
        radius: height / 2
        color: root.trackColor

        Rectangle {
            width: root.computedFillWidth
            height: parent.height
            radius: parent.radius
            color: root.fillColor
            visible: width > 0

            Behavior on width {
                enabled: root.animated
                NumberAnimation {
                    duration: 220
                    easing.type: Easing.OutCubic
                }
            }
        }
    }
}
