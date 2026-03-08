import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3

RowLayout {
    id: root

    property var tokens: null
    property bool providerStatusVisible: false
    property string providerStatusBadge: ""
    property string providerStatusDetails: ""
    property string providerStatusTone: "warn"
    readonly property color providerStatusColor: providerStatusTone === "error" ? tokens.error : tokens.warn

    Layout.fillWidth: true
    spacing: tokens.spacing.chipGap
    visible: providerStatusVisible && providerStatusBadge !== ""

    Rectangle {
        radius: tokens.radius.chip
        implicitHeight: tokens.chipHeight
        implicitWidth: statusBadgeText.implicitWidth + tokens.chipHorizontalPadding
        color: Qt.rgba(root.providerStatusColor.r, root.providerStatusColor.g, root.providerStatusColor.b, 0.18)
        border.width: 1
        border.color: Qt.rgba(root.providerStatusColor.r, root.providerStatusColor.g, root.providerStatusColor.b, 0.32)

        PC3.Label {
            id: statusBadgeText
            anchors.centerIn: parent
            text: root.providerStatusBadge
            color: root.providerStatusColor
            font.pixelSize: tokens.metaTextSize - 1
            font.bold: true
        }
    }

    PC3.Label {
        Layout.fillWidth: true
        visible: root.providerStatusDetails !== ""
        text: root.providerStatusDetails
        color: tokens.mutedText
        font.pixelSize: tokens.metaTextSize - 1
        elide: Text.ElideRight
    }
}
