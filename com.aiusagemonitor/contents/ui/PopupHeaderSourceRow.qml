import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3

RowLayout {
    id: root

    property var tokens: null
    property string sourceModeLabel: ""
    property string activeSourceLabel: ""
    property var sourceStatusTags: []

    Layout.fillWidth: true
    spacing: tokens.spacing.chipGap
    visible: sourceModeLabel !== "" || activeSourceLabel !== "" || sourceStatusTags.length > 0

    Rectangle {
        visible: root.sourceModeLabel !== ""
        radius: tokens.radius.chipPrimary
        implicitHeight: tokens.chipPrimaryHeight
        implicitWidth: sourceModeText.implicitWidth + tokens.chipPrimaryHorizontalPadding
        color: Qt.rgba(tokens.accent.r, tokens.accent.g, tokens.accent.b, 0.18)
        border.width: 1
        border.color: Qt.rgba(tokens.accent.r, tokens.accent.g, tokens.accent.b, 0.34)

        PC3.Label {
            id: sourceModeText
            anchors.centerIn: parent
            text: root.sourceModeLabel
            color: tokens.text
            font.pixelSize: tokens.metaTextSize - 1
            font.bold: true
        }
    }

    Rectangle {
        visible: root.activeSourceLabel !== ""
        radius: tokens.radius.chip
        implicitHeight: tokens.chipHeight
        implicitWidth: activeSourceText.implicitWidth + tokens.chipHorizontalPadding
        color: Qt.rgba(tokens.raisedSurface.r, tokens.raisedSurface.g, tokens.raisedSurface.b, 0.30)
        border.width: 1
        border.color: Qt.rgba(tokens.text.r, tokens.text.g, tokens.text.b, 0.16)

        PC3.Label {
            id: activeSourceText
            anchors.centerIn: parent
            text: root.activeSourceLabel
            color: tokens.mutedText
            font.pixelSize: tokens.metaTextSize - 1
        }
    }

    Repeater {
        model: root.sourceStatusTags

        delegate: Rectangle {
            required property var modelData
            radius: tokens.radius.chip
            implicitHeight: tokens.chipHeight
            implicitWidth: statusText.implicitWidth + tokens.chipHorizontalPadding
            color: Qt.rgba(tokens.raisedSurface.r, tokens.raisedSurface.g, tokens.raisedSurface.b, 0.24)
            border.width: 1
            border.color: Qt.rgba(tokens.text.r, tokens.text.g, tokens.text.b, 0.12)

            PC3.Label {
                id: statusText
                anchors.centerIn: parent
                text: String(modelData || "")
                color: tokens.mutedText
                font.pixelSize: tokens.metaTextSize - 1
            }
        }
    }
}
