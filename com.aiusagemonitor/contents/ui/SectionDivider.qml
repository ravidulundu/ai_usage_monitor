import QtQuick
import QtQuick.Layouts

Rectangle {
    id: root
    PopupTokens {
        id: tokens
    }

    Layout.fillWidth: true
    implicitHeight: tokens.dividerThickness
    color: tokens.separator
}
