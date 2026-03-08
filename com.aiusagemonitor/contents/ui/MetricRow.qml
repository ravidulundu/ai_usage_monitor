import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3

ColumnLayout {
    id: root

    PopupTokens {
        id: tokens
    }

    property var metric: ({})
    property bool showDivider: true
    readonly property string metricToneKey: (metric && metric.tone) ? metric.tone : "accent"
    readonly property bool metricAvailable: metric && metric.available === true

    function toneColor(toneKey) {
        if (toneKey === "error")
            return tokens.error
        if (toneKey === "warn")
            return tokens.warn
        return tokens.accent
    }

    readonly property color metricTone: toneColor(metricToneKey)
    readonly property color secondaryTone: metricToneKey === "error"
        ? tokens.error
        : (metricToneKey === "warn" ? tokens.warn : tokens.mutedText)

    Layout.fillWidth: true
    spacing: tokens.spacing.rowGap

    PC3.Label {
        text: (root.metric && root.metric.label) ? root.metric.label : ""
        font.pixelSize: tokens.titleTextSize
        font.bold: true
    }

    ProgressLine {
        percentValue: (root.metric && root.metric.percent !== undefined && root.metric.percent !== null)
            ? root.metric.percent
            : null
        thickness: tokens.progressThickness
        fillColor: root.metricTone
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: tokens.spacing.metricInlineGap

        Rectangle {
            width: tokens.metricDotSize
            height: tokens.metricDotSize
            radius: width / 2
            color: root.metricAvailable
                ? root.metricTone
                : tokens.mutedText
        }

        PC3.Label {
            text: (root.metric && root.metric.leftText) ? root.metric.leftText : ""
            font.pixelSize: tokens.metaTextSize
            color: root.metricAvailable ? tokens.text : tokens.mutedText
        }

        Item {
            Layout.fillWidth: true
        }

        PC3.Label {
            text: (root.metric && root.metric.rightText) ? root.metric.rightText : ""
            font.pixelSize: tokens.metaTextSize
            color: tokens.mutedText
        }
    }

    PC3.Label {
        Layout.fillWidth: true
        text: (root.metric && root.metric.secondaryText) ? root.metric.secondaryText : ""
        visible: text !== ""
        font.pixelSize: tokens.metaTextSize
        color: root.secondaryTone
    }

    SectionDivider {
        visible: root.showDivider
    }
}
