import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3

Rectangle {
    id: root

    PopupTokens {
        id: tokens
    }

    property string message: ""

    radius: tokens.radius.card
    color: tokens.cardSurface
    border.width: 1
    border.color: tokens.separator
    implicitHeight: tokens.emptyStateHeight

    PC3.Label {
        anchors.centerIn: parent
        width: tokens.emptyStateMessageWidth
        wrapMode: Text.Wrap
        horizontalAlignment: Text.AlignHCenter
        text: root.message
        color: tokens.mutedText
    }
}
