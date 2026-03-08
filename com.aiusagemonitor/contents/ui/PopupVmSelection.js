function filteredTabs(rawTabs) {
    var source = rawTabs || []
    var filtered = []
    for (var i = 0; i < source.length; i++) {
        var tab = source[i]
        if (!tab || tab.visible === false || tab.enabled === false)
            continue
        filtered.push(tab)
    }
    return filtered
}

function hasOverviewTab(tabsModel) {
    for (var i = 0; i < tabsModel.length; i++) {
        if (tabsModel[i].id === "overview")
            return true
    }
    return false
}

function providerForId(providersModel, providerId) {
    if (!providerId)
        return null
    var providers = providersModel || []
    for (var i = 0; i < providers.length; i++) {
        if (providers[i].id === providerId)
            return providers[i]
    }
    return null
}

function providerOrder(popupData, tabsModel) {
    var ids = Array.isArray(popupData.selectableProviderIds) ? popupData.selectableProviderIds : []
    if (ids.length > 0)
        return ids
    var ordered = []
    for (var i = 0; i < tabsModel.length; i++) {
        var tab = tabsModel[i]
        if (tab.kind === "provider")
            ordered.push(tab.id)
    }
    return ordered
}

function resolveSelectedProviderId(tabsModel, popupData, requestedId) {
    var selectableTabs = tabsModel || []
    if (selectableTabs.length === 0)
        return ""

    if (requestedId) {
        for (var i = 0; i < selectableTabs.length; i++) {
            if (selectableTabs[i].id === requestedId)
                return requestedId
        }
    }

    var vmSelectedId = popupData.selectedProviderId || ""
    if (vmSelectedId) {
        for (i = 0; i < selectableTabs.length; i++) {
            if (selectableTabs[i].id === vmSelectedId)
                return vmSelectedId
        }
    }

    for (i = 0; i < selectableTabs.length; i++) {
        if (selectableTabs[i].kind === "provider")
            return selectableTabs[i].id
    }
    return selectableTabs[0].id || ""
}
