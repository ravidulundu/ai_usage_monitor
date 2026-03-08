import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.components as PC3

ColumnLayout {
    id: root

    PopupTokens {
        id: tokens
    }

    property var cardsModel: []
    property string emptyMessage: "No AI tools detected"
    signal providerSelected(string providerId)

    Layout.fillWidth: true
    spacing: tokens.spacing.compactSectionGap

    Loader {
        Layout.fillWidth: true
        active: (root.cardsModel || []).length === 0

        sourceComponent: EmptyStateCard {
            message: root.emptyMessage
        }
    }

    Repeater {
        model: root.cardsModel || []

        delegate: QQC2.AbstractButton {
            required property var modelData
            readonly property var card: modelData

            onClicked: root.providerSelected(card.providerId || "")

            background: Rectangle {
                radius: tokens.radius.card
                color: tokens.cardSurface
                border.width: 1
                border.color: tokens.separator
            }

            contentItem: ColumnLayout {
                spacing: tokens.spacing.rowGap

                RowLayout {
                    Layout.fillWidth: true

                    PC3.Label {
                        text: card.title || ""
                        font.pixelSize: tokens.overviewTitleTextSize
                        font.bold: true
                        color: tokens.text
                    }

                    Item {
                        Layout.fillWidth: true
                    }

                    PC3.Label {
                        text: card.planLabel || ""
                        visible: text !== ""
                        color: tokens.mutedText
                        font.pixelSize: tokens.tabTextSize
                    }
                }

                Repeater {
                    model: card.metrics || []

                    delegate: OverviewMetricRow {
                        required property var modelData
                        metric: modelData
                    }
                }
            }
        }
    }
}
