import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3

ColumnLayout {
    id: root

    property var tokens: null
    property string title: ""
    property string message: ""

    spacing: root.tokens ? root.tokens.spacing.rowGap : 6

    PC3.Label {
        text: root.title
        visible: text !== ""
        font.pixelSize: root.tokens ? root.tokens.titleTextSize - 1 : 12
        font.bold: true
        color: root.tokens ? root.tokens.text : "white"
    }

    PC3.Label {
        Layout.fillWidth: true
        text: root.message
        visible: text !== ""
        wrapMode: Text.Wrap
        color: root.tokens ? root.tokens.mutedText : "#c0c0c0"
        font.pixelSize: root.tokens ? root.tokens.metaTextSize : 11
    }
}
