import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: root

    PopupTokens {
        id: tokens
    }

    property var provider: null
    property bool forceSwitchingState: false
    property var actionsModel: []
    signal actionTriggered(var actionData)

    readonly property var providerSwitchingState: (root.provider && root.provider.switchingState)
        ? root.provider.switchingState
        : ({})
    readonly property bool switchingActive: root.forceSwitchingState || providerSwitchingState.active === true
    readonly property string switchingTitle: {
        var title = providerSwitchingState.title || ""
        if (title !== "")
            return title
        return switchingActive ? "Switching account/source" : ""
    }
    readonly property string switchingMessage: {
        var message = providerSwitchingState.message || ""
        if (message !== "")
            return message
        return switchingActive ? "Refreshing usage for active identity" : ""
    }
    readonly property var metricsModel: root.provider ? (root.provider.metrics || []) : []
    readonly property bool hasMetrics: !switchingActive && root.metricsModel.length > 0
    readonly property bool hasExtraUsage: !switchingActive
        && root.provider
        && root.provider.extraUsage
        && root.provider.extraUsage.visible
    readonly property bool hasCost: !switchingActive
        && root.provider
        && root.provider.cost
        && root.provider.cost.visible
    readonly property bool hasActions: (root.actionsModel || []).length > 0

    Layout.fillWidth: true
    spacing: tokens.spacing.compactSectionGap

    PopupHeader {
        provider: root.provider
    }

    SectionDivider {
        visible: root.switchingActive || root.hasMetrics || root.hasExtraUsage || root.hasCost || root.hasActions
    }

    Loader {
        Layout.fillWidth: true
        active: root.switchingActive

        sourceComponent: ProviderSwitchingNotice {
            tokens: tokens
            title: root.switchingTitle
            message: root.switchingMessage
        }
    }

    Repeater {
        model: root.metricsModel

        delegate: MetricRow {
            required property int index
            required property var modelData

            metric: modelData
            showDivider: index < (root.metricsModel.length - 1)
        }
    }

    SectionDivider {
        visible: !root.switchingActive && root.hasMetrics && (root.hasExtraUsage || root.hasCost || root.hasActions)
    }

    Loader {
        Layout.fillWidth: true
        active: root.hasExtraUsage

        sourceComponent: CostSection {
            title: root.provider.extraUsage.title
            rows: root.provider.extraUsage.rows || []
        }
    }

    SectionDivider {
        visible: !root.switchingActive && root.hasExtraUsage && (root.hasCost || root.hasActions)
    }

    Loader {
        Layout.fillWidth: true
        active: root.hasCost

        sourceComponent: CostSection {
            title: root.provider.cost.title
            rows: root.provider.cost.rows || []
            showChevron: true
        }
    }

    SectionDivider {
        visible: (root.switchingActive && root.hasActions)
            || (!root.switchingActive && root.hasCost && root.hasActions)
    }

    Loader {
        Layout.fillWidth: true
        active: root.hasActions

        sourceComponent: ProviderActionsSection {
            tokens: tokens
            actionsModel: root.actionsModel
            onActionTriggered: function(actionData) {
                root.actionTriggered(actionData)
            }
        }
    }
}
