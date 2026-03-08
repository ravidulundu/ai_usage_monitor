.pragma library

function sourceDisplayToken(sourceId) {
    var normalized = String(sourceId || "").toLowerCase()
    if (normalized === "local_cli")
        return "LOCAL CLI"
    return String(sourceId || "").toUpperCase()
}

function settingsPresentationFromLive(liveState) {
    var sourceModel = sourceModelFromLive(liveState)
    if (sourceModel && sourceModel.settingsPresentation)
        return sourceModel.settingsPresentation
    return null
}

function sourceModeOptions(descriptor) {
    var modes = (descriptor && descriptor.sourceModes) ? descriptor.sourceModes.slice(0) : []
    var supportsLocal = modes.indexOf("cli") !== -1 || modes.indexOf("local") !== -1 || modes.indexOf("oauth") !== -1
    var supportsRemote = modes.indexOf("api") !== -1 || modes.indexOf("web") !== -1 || modes.indexOf("remote") !== -1
    if (supportsLocal && supportsRemote && modes.indexOf("local_cli") === -1)
        modes.unshift("local_cli")
    return modes
}

function sourceOptionItems(descriptor) {
    var modes = sourceModeOptions(descriptor)
    var items = []
    for (var i = 0; i < modes.length; i++) {
        var mode = String(modes[i] || "")
        var label = mode === "local_cli"
            ? "Local-first (CLI→API)"
            : String(mode).toUpperCase()
        items.push({ "value": mode, "label": label })
    }
    return items
}

function defaultPreferredSource(descriptor) {
    var options = sourceModeOptions(descriptor)
    return options.length > 0 ? options[0] : "auto"
}

function sourceModelFromLive(liveState) {
    return (liveState && liveState.sourceModel) ? liveState.sourceModel : null
}

function strategyFromLive(providerState, liveState) {
    var sourceModel = sourceModelFromLive(liveState)
    if (sourceModel && sourceModel.sourceStrategy)
        return sourceModel.sourceStrategy
    return {
        preferredSource: providerState && providerState.source ? providerState.source : "auto",
        resolvedSource: sourceModel && sourceModel.activeSource ? sourceModel.activeSource : (providerState && providerState.source ? providerState.source : "auto"),
        fallbackReason: null,
        resolutionReason: "default_source",
        fallbackActive: false
    }
}

function descriptorCapabilities(descriptor) {
    var modes = (descriptor && descriptor.sourceModes) ? descriptor.sourceModes : []
    var supportsLocalCli = modes.indexOf("cli") !== -1 || modes.indexOf("local") !== -1 || modes.indexOf("oauth") !== -1
    var supportsApi = modes.indexOf("api") !== -1
    var supportsWeb = modes.indexOf("web") !== -1 || modes.indexOf("remote") !== -1
    return {
        supportsLocalCli: supportsLocalCli,
        supportsApi: supportsApi,
        supportsWeb: supportsWeb
    }
}

function humanizeReason(value) {
    if (!value)
        return ""
    return String(value).replace(/_/g, " ")
}

function providerRowSubtitle(descriptor, providerState, liveState) {
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.subtitle)
        return settingsPresentation.subtitle

    var sourceModel = sourceModelFromLive(liveState)
    var sourceLabel = (sourceModel && sourceModel.sourceLabel)
        ? sourceModel.sourceLabel
        : ((providerState && providerState.source)
            ? sourceDisplayToken(providerState.source)
            : ((sourceModeOptions(descriptor).length > 0)
                ? sourceDisplayToken(sourceModeOptions(descriptor)[0])
                : "AUTO"))
    return sourceLabel + " source"
}

function providerCapabilitiesText(descriptor, liveState) {
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.capabilitiesLabel)
        return settingsPresentation.capabilitiesLabel

    var sourceModel = sourceModelFromLive(liveState)
    var capabilities = (sourceModel && sourceModel.providerCapabilities)
        ? sourceModel.providerCapabilities
        : ((descriptor && descriptor.providerCapabilities) ? descriptor.providerCapabilities : descriptorCapabilities(descriptor))
    var labels = []
    if (capabilities && capabilities.supportsLocalCli)
        labels.push("Local CLI")
    if (capabilities && capabilities.supportsApi)
        labels.push("API")
    if (capabilities && capabilities.supportsWeb)
        labels.push("Web")
    return labels.length > 0 ? labels.join(" + ") : "Unavailable"
}

function providerStrategyText(providerState, liveState) {
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.strategyLabel)
        return settingsPresentation.strategyLabel

    var strategy = strategyFromLive(providerState, liveState)
    var preferred = strategy && strategy.preferredSource ? strategy.preferredSource : (providerState && providerState.source ? providerState.source : "auto")
    var resolved = strategy && strategy.resolvedSource ? strategy.resolvedSource : preferred
    return "Preferred " + sourceDisplayToken(preferred) + " · Active " + sourceDisplayToken(resolved)
}

function providerAvailabilityText(descriptor, providerState, liveState) {
    void descriptor
    void providerState
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.availabilityLabel)
        return settingsPresentation.availabilityLabel

    return "Unknown"
}

function providerSourceModeLabel(descriptor, providerState, liveState) {
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.sourceModeLabel)
        return settingsPresentation.sourceModeLabel

    var sourceModel = sourceModelFromLive(liveState)
    if (sourceModel && sourceModel.sourceLabel)
        return sourceModel.sourceLabel
    var source = providerState && providerState.source ? providerState.source : defaultPreferredSource(descriptor)
    if (String(source || "").toLowerCase() === "local_cli")
        return "Local-first"
    return sourceDisplayToken(source)
}

function providerActiveSourceLabel(providerState, liveState) {
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.activeSourceLabel)
        return settingsPresentation.activeSourceLabel

    var sourceModel = sourceModelFromLive(liveState)
    var strategy = strategyFromLive(providerState, liveState)
    var resolved = strategy && strategy.resolvedSource ? strategy.resolvedSource : (sourceModel && sourceModel.activeSource ? sourceModel.activeSource : (providerState && providerState.source ? providerState.source : "auto"))
    return "Active " + sourceDisplayToken(resolved)
}

function providerPreferredSourceLabel(providerState, liveState) {
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.preferredSourceLabel)
        return settingsPresentation.preferredSourceLabel

    var strategy = strategyFromLive(providerState, liveState)
    var preferred = strategy && strategy.preferredSource
        ? strategy.preferredSource
        : (providerState && providerState.source ? providerState.source : "auto")
    return "Preferred " + sourceDisplayToken(preferred)
}

function providerSourceStatusLabel(descriptor, providerState, liveState) {
    void descriptor
    void providerState
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.sourceStatusLabel)
        return settingsPresentation.sourceStatusLabel

    return ""
}

function providerFallbackLabel(providerState, liveState) {
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.fallbackLabel)
        return settingsPresentation.fallbackLabel
    return ""
}

function providerStatusTags(descriptor, providerState, liveState) {
    void descriptor
    void providerState
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.statusTags)
        return settingsPresentation.statusTags

    return []
}

function providerSourceReason(providerState, liveState) {
    void providerState
    var settingsPresentation = settingsPresentationFromLive(liveState)
    if (settingsPresentation && settingsPresentation.sourceReasonLabel)
        return settingsPresentation.sourceReasonLabel
    if (settingsPresentation && settingsPresentation.fallbackLabel)
        return settingsPresentation.fallbackLabel

    return ""
}
