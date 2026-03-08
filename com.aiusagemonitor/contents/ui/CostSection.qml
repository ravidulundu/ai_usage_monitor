import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3

ColumnLayout {
    id: root

    PopupTokens {
        id: tokens
    }

    property string title: ""
    property var rows: []
    property bool showChevron: false

    Layout.fillWidth: true
    spacing: tokens.spacing.rowGap

    RowLayout {
        Layout.fillWidth: true

        PC3.Label {
            text: root.title
            font.pixelSize: tokens.titleTextSize
            font.bold: true
            color: tokens.text
        }

        Item {
            Layout.fillWidth: true
        }

        PC3.Label {
            text: "›"
            visible: root.showChevron
            font.pixelSize: tokens.titleTextSize
            color: tokens.mutedText
        }
    }

    Repeater {
        model: root.rows || []

        delegate: ColumnLayout {
            required property var modelData
            Layout.fillWidth: true
            spacing: tokens.spacing.rowGap

            RowLayout {
                Layout.fillWidth: true
                spacing: tokens.spacing.inlineGap

                PC3.Label {
                    text: (modelData && modelData.label) ? modelData.label : ""
                    visible: text !== ""
                    color: tokens.text
                    font.pixelSize: tokens.metaTextSize
                }

                Item {
                    Layout.fillWidth: true
                }

                PC3.Label {
                    text: (modelData && modelData.value) ? modelData.value : ""
                    color: tokens.text
                    font.pixelSize: tokens.metaTextSize
                    font.bold: true
                }
            }

            PC3.Label {
                text: (modelData && modelData.meta) ? modelData.meta : ""
                visible: text !== ""
                color: tokens.mutedText
                font.pixelSize: tokens.metaTextSize
            }
        }
    }
}
