import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3

RowLayout {
    id: root

    PopupTokens {
        id: tokens
    }

    property var metric: ({})

    Layout.fillWidth: true

    PC3.Label {
        text: (root.metric && root.metric.label) ? root.metric.label : ""
        font.pixelSize: tokens.tabTextSize
        color: tokens.mutedText
    }

    ProgressLine {
        Layout.fillWidth: true
        thickness: tokens.progressThickness
        animated: false
        percentValue: (root.metric && root.metric.available) ? root.metric.percent : null
        fillColor: tokens.accent
    }

    PC3.Label {
        text: (root.metric && root.metric.displayText) ? root.metric.displayText : "—"
        font.pixelSize: tokens.tabTextSize
        font.bold: true
        color: tokens.text
    }
}
