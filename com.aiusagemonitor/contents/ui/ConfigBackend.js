function deepClone(config) {
    return JSON.parse(JSON.stringify(config || {
        version: 1,
        refreshInterval: 60,
        overviewProviderIds: [],
        providers: [],
    }))
}

function shellQuote(value) {
    return "'" + String(value).replace(/'/g, "'\"'\"'") + "'"
}

function providerForPanelModel(descriptors) {
    var providers = descriptors && descriptors.length > 0 ? descriptors : [
        { id: "claude", displayName: "Claude Code", shortName: "Claude" },
        { id: "codex", displayName: "OpenAI Codex", shortName: "Codex" },
        { id: "gemini", displayName: "Gemini CLI", shortName: "Gemini" },
        { id: "copilot", displayName: "GitHub Copilot", shortName: "Copilot" },
        { id: "vertexai", displayName: "Vertex AI", shortName: "Vertex" },
        { id: "openrouter", displayName: "OpenRouter", shortName: "OpenRouter" },
        { id: "ollama", displayName: "Ollama", shortName: "Ollama" },
        { id: "opencode", displayName: "OpenCode", shortName: "OpenCode" },
        { id: "zai", displayName: "z.ai", shortName: "z.ai" },
        { id: "kilo", displayName: "Kilo Code", shortName: "Kilo" },
        { id: "minimax", displayName: "MiniMax", shortName: "MiniMax" },
        { id: "amp", displayName: "Amp", shortName: "Amp" },
    ]
    return [{ id: "auto", displayName: "Auto (active)", shortName: "Auto" }].concat(providers)
}

function providerLiveState(stateProviders, providerId) {
    for (var i = 0; i < stateProviders.length; i++) {
        if (stateProviders[i].id === providerId)
            return stateProviders[i]
    }
    return null
}

function providerIcon(descriptor) {
    var branding = descriptor && descriptor.branding ? descriptor.branding : {}
    var assetName = branding.assetName || ""
    if (!assetName && branding.iconKey)
        assetName = branding.iconKey + ".svg"
    return assetName ? Qt.resolvedUrl("../images/" + assetName) : ""
}

function sharedProviderState(sharedProviders, descriptors, providerId, defaultSource) {
    for (var i = 0; i < sharedProviders.length; i++) {
        if (sharedProviders[i].id === providerId)
            return sharedProviders[i]
    }
    for (var d = 0; d < descriptors.length; d++) {
        if (descriptors[d].id === providerId) {
            return {
                id: providerId,
                enabled: descriptors[d].defaultEnabled,
                source: defaultSource(descriptors[d]),
            }
        }
    }
    return { id: providerId, enabled: true, source: "auto" }
}

function setProviderField(stagedConfig, providerId, field, value) {
    var config = deepClone(stagedConfig)
    if (!config.providers)
        config.providers = []

    var found = false
    for (var i = 0; i < config.providers.length; i++) {
        if (config.providers[i].id !== providerId)
            continue
        if (value === "" || value === null || value === undefined)
            delete config.providers[i][field]
        else
            config.providers[i][field] = value
        found = true
        break
    }

    if (!found) {
        var entry = { id: providerId }
        if (!(value === "" || value === null || value === undefined))
            entry[field] = value
        config.providers.push(entry)
    }

    return config
}

function selectedOverviewIds(stagedConfig) {
    if (stagedConfig && stagedConfig.overviewProviderIds && Array.isArray(stagedConfig.overviewProviderIds))
        return stagedConfig.overviewProviderIds
    return []
}

function isOverviewSelected(stagedConfig, providerId) {
    return selectedOverviewIds(stagedConfig).indexOf(providerId) !== -1
}

function toggleOverviewProvider(stagedConfig, providerId, enabled, maxCount) {
    var config = deepClone(stagedConfig)
    var selected = Array.isArray(config.overviewProviderIds) ? config.overviewProviderIds.slice(0, maxCount) : []
    var idx = selected.indexOf(providerId)
    if (enabled) {
        if (idx === -1 && selected.length < maxCount)
            selected.push(providerId)
    } else if (idx !== -1) {
        selected.splice(idx, 1)
    }
    config.overviewProviderIds = selected
    return config
}

function syncConfigFromPayload(payload, currentConfig) {
    var nextConfig = currentConfig
    var nextProviders = []
    if (payload.config && payload.config.providers) {
        nextProviders = payload.config.providers
        nextConfig = deepClone(payload.config)
    }
    return {
        stagedConfig: nextConfig,
        sharedProviders: nextProviders,
    }
}
