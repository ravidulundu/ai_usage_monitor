import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts

QQC2.ItemDelegate {
    id: root

    PopupTokens {
        id: tokens
    }

    property var actionData: ({})
    signal triggered(var actionData)

    function iconNameFor(actionId) {
        switch (actionId) {
        case "usage_dashboard":
            return "view-statistics"
        case "status_page":
            return "network-server"
        case "settings":
            return "settings-configure"
        case "about":
            return "help-about"
        case "quit":
            return "application-exit"
        default:
            return "go-next"
        }
    }

    Layout.fillWidth: true
    implicitHeight: tokens.rowHeight
    text: (actionData && actionData.label) ? actionData.label : ""
    enabled: actionData ? actionData.enabled === true : false
    icon.name: iconNameFor(actionData ? actionData.id : "")
    icon.width: tokens.actionIconSize
    icon.height: tokens.actionIconSize
    font.pixelSize: tokens.metaTextSize
    leftPadding: tokens.actionHorizontalPadding
    rightPadding: tokens.actionHorizontalPadding
    topPadding: tokens.actionVerticalPadding
    bottomPadding: tokens.actionVerticalPadding

    background: Rectangle {
        radius: tokens.radius.actionPill
        color: root.pressed
            ? tokens.selectedTabSurface
            : (root.hovered ? tokens.actionHoverSurface : "transparent")
        border.width: root.hovered ? 1 : 0
        border.color: root.hovered ? tokens.separator : "transparent"
    }

    onClicked: root.triggered(root.actionData)
}
