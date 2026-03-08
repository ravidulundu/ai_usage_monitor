import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC3

ColumnLayout {
    id: root

    property var tokens: null
    property var actionsModel: []
    signal actionTriggered(var actionData)

    spacing: root.tokens ? root.tokens.spacing.rowGap : 6

    PC3.Label {
        text: "Actions"
        font.pixelSize: root.tokens ? root.tokens.titleTextSize : 12
        font.bold: true
        color: root.tokens ? root.tokens.text : "white"
    }

    ActionList {
        Layout.fillWidth: true
        actionsModel: root.actionsModel
        onActionTriggered: function(actionData) {
            root.actionTriggered(actionData)
        }
    }
}
