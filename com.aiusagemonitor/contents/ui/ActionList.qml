import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: root

    PopupTokens {
        id: tokens
    }

    property var actionsModel: []
    signal actionTriggered(var actionData)

    Layout.fillWidth: true
    spacing: tokens.spacing.actionRowGap
    visible: (actionsModel || []).length > 0

    Repeater {
        model: root.actionsModel || []

        delegate: ActionRow {
            required property var modelData
            actionData: modelData
            onTriggered: root.actionTriggered(actionData)
        }
    }
}
