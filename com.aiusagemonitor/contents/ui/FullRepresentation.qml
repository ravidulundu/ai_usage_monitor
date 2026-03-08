import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid

import "PopupVmSelection.js" as PopupVmSelection

Item {
    id: fullRoot

    PopupTokens { id: tokens }
    ActionDispatcher { id: actionDispatcher }

    implicitWidth: tokens.width
    implicitHeight: contentCol.implicitHeight + tokens.spacing.outerPadding + tokens.contentBottomPadding
    width: implicitWidth
    height: implicitHeight

    property string selectedProviderId: ""

    readonly property var popupData: root.popupData || ({})
    readonly property var rawTabsModel: popupData.switcherTabs || popupData.tabs || []
    readonly property var tabsModel: PopupVmSelection.filteredTabs(rawTabsModel)
    readonly property bool hasOverviewTab: PopupVmSelection.hasOverviewTab(tabsModel)
    readonly property var overviewCardsModel: popupData.overviewCards || []
    readonly property var providersModel: popupData.providers || []
    readonly property var providerOrderModel: PopupVmSelection.providerOrder(popupData, tabsModel)
    readonly property var selectedProviderData: selectedProviderId === "overview"
        ? null
        : PopupVmSelection.providerForId(providersModel, selectedProviderId)
    readonly property bool selectedOverviewTab: selectedProviderId === "overview"
    readonly property bool selectedIdentityMismatch: {
        if (!selectedProviderId)
            return false
        var mismatchMap = root.identityMismatchByProvider || ({})
        return mismatchMap[selectedProviderId] === true
    }
    readonly property var selectedActionsModel: actionDispatcher.visibleActions(
        selectedProviderData ? selectedProviderData.actions : []
    )
    readonly property string emptyStateMessage: {
        if (root.isLoading)
            return "Loading..."
        if (root.lastError)
            return root.lastError
        if (selectedOverviewTab && overviewCardsModel.length === 0)
            return "No overview providers selected"
        if (providerOrderModel.length === 0 && !hasOverviewTab)
            return "No supported providers detected"
        return "No AI tools detected"
    }

    function selectProvider(requestedId) {
        var resolved = PopupVmSelection.resolveSelectedProviderId(tabsModel, popupData, requestedId)
        if (resolved !== selectedProviderId)
            selectedProviderId = resolved
    }

    function syncSelectedProvider() {
        selectProvider(selectedProviderId)
    }

    onTabsModelChanged: syncSelectedProvider()
    onPopupDataChanged: syncSelectedProvider()
    Component.onCompleted: syncSelectedProvider()

    Rectangle {
        anchors.fill: parent
        radius: tokens.radius.surface
        color: tokens.surface
        border.width: 1
        border.color: tokens.separator
    }

    ColumnLayout {
        id: contentCol
        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
            margins: tokens.spacing.outerPadding
        }
        spacing: tokens.spacing.sectionGap

        ProviderTabsRow {
            Layout.fillWidth: true
            visible: fullRoot.tabsModel.length > 0
            tabsModel: fullRoot.tabsModel
            selectedTabId: fullRoot.selectedProviderId
            onTabSelected: function(tabId) { fullRoot.selectProvider(tabId) }
        }

        Loader {
            Layout.fillWidth: true
            active: fullRoot.selectedOverviewTab
            sourceComponent: OverviewCardsSection {
                cardsModel: fullRoot.overviewCardsModel
                emptyMessage: fullRoot.emptyStateMessage
                onProviderSelected: function(providerId) { fullRoot.selectProvider(providerId) }
            }
        }

        Loader {
            Layout.fillWidth: true
            active: !!fullRoot.selectedProviderData
            sourceComponent: ProviderDetailSection {
                provider: fullRoot.selectedProviderData
                forceSwitchingState: fullRoot.selectedIdentityMismatch
                actionsModel: fullRoot.selectedActionsModel
                onActionTriggered: function(actionData) { actionDispatcher.dispatch(actionData) }
            }
        }

        Loader {
            Layout.fillWidth: true
            active: !fullRoot.selectedOverviewTab && !fullRoot.selectedProviderData
            sourceComponent: EmptyStateCard { message: fullRoot.emptyStateMessage }
        }
    }
}
