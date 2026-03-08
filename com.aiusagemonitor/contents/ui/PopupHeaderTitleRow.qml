import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3

RowLayout {
    id: root

    property var provider: null
    property var tokens: null

    Layout.fillWidth: true
    spacing: tokens.spacing.inlineGap

    ColumnLayout {
        spacing: 1

        PC3.Label {
            text: (root.provider && root.provider.displayName) ? root.provider.displayName : ""
            font.pixelSize: tokens.headerTitleTextSize
            font.bold: true
            color: tokens.text
        }

        PC3.Label {
            text: (root.provider && root.provider.updatedText) ? root.provider.updatedText : ""
            color: tokens.mutedText
            font.pixelSize: tokens.metaTextSize
        }
    }

    Item { Layout.fillWidth: true }

    PC3.Label {
        text: (root.provider && root.provider.planLabel) ? root.provider.planLabel : ""
        visible: text !== ""
        color: tokens.mutedText
        font.pixelSize: tokens.metaTextSize
    }
}
