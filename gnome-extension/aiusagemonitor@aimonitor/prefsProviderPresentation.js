function settingsPresentation(providerState) {
    return providerState?.sourceModel?.settingsPresentation || null;
}

export function providerSubtitle(descriptor, providerState) {
    const presentation = settingsPresentation(providerState);
    if (presentation?.subtitle)
        return presentation.subtitle;

    const sourceMode = providerSourceModeLabel(descriptor, providerState);
    return `${sourceMode} source`;
}

export function humanizeReason(value) {
    if (!value)
        return '';
    return String(value).replace(/_/g, ' ');
}

export function descriptorCapabilities(descriptor) {
    const sourceModes = Array.isArray(descriptor?.sourceModes) ? descriptor.sourceModes : [];
    return {
        supportsLocalCli: sourceModes.some(mode => ['cli', 'local', 'oauth'].includes(mode)),
        supportsApi: sourceModes.includes('api'),
        supportsWeb: sourceModes.some(mode => ['web', 'remote'].includes(mode)),
    };
}

export function sourceModeOptions(descriptor) {
    const sourceModes = Array.isArray(descriptor?.sourceModes) ? [...descriptor.sourceModes] : [];
    const supportsLocal = sourceModes.some(mode => ['cli', 'local', 'oauth'].includes(mode));
    const supportsRemote = sourceModes.some(mode => ['api', 'web', 'remote'].includes(mode));
    if (supportsLocal && supportsRemote && !sourceModes.includes('local_cli'))
        sourceModes.unshift('local_cli');
    return sourceModes;
}

export function sourceModeDisplayLabel(mode) {
    if (String(mode || '').toLowerCase() === 'local_cli')
        return 'LOCAL-FIRST (CLI→API)';
    return String(mode || '').toUpperCase();
}

export function sourceToken(mode) {
    if (String(mode || '').toLowerCase() === 'local_cli')
        return 'LOCAL CLI';
    return String(mode || '').toUpperCase();
}

export function providerCapabilitiesText(descriptor, providerState) {
    const presentation = settingsPresentation(providerState);
    if (presentation?.capabilitiesLabel)
        return presentation.capabilitiesLabel;

    const sourceModel = providerState?.sourceModel;
    const capabilities = sourceModel?.providerCapabilities || descriptor?.providerCapabilities || descriptorCapabilities(descriptor);
    const labels = [];
    if (capabilities?.supportsLocalCli)
        labels.push('Local CLI');
    if (capabilities?.supportsApi)
        labels.push('API');
    if (capabilities?.supportsWeb)
        labels.push('Web');
    return labels.length > 0 ? labels.join(' + ') : 'Unavailable';
}

export function providerSourceModeLabel(descriptor, providerState) {
    const presentation = settingsPresentation(providerState);
    if (presentation?.sourceModeLabel)
        return presentation.sourceModeLabel;

    const sourceModel = providerState?.sourceModel;
    if (sourceModel?.sourceLabel)
        return sourceModel.sourceLabel;
    const sourceModes = sourceModeOptions(descriptor);
    if (sourceModes.length > 0)
        return sourceModeDisplayLabel(sourceModes[0]);
    return 'AUTO';
}

export function providerActiveSourceLabel(descriptor, providerState) {
    const presentation = settingsPresentation(providerState);
    if (presentation?.activeSourceLabel)
        return presentation.activeSourceLabel;

    const sourceModel = providerState?.sourceModel;
    const strategy = sourceModel?.sourceStrategy;
    const resolved = strategy?.resolvedSource || sourceModel?.activeSource || descriptor?.sourceModes?.[0] || 'auto';
    return `Active ${sourceToken(resolved)}`;
}

export function providerPreferredSourceLabel(providerSettings, providerState) {
    const presentation = settingsPresentation(providerState);
    if (presentation?.preferredSourceLabel)
        return presentation.preferredSourceLabel;

    const sourceModel = providerState?.sourceModel;
    const strategy = sourceModel?.sourceStrategy;
    const preferred = strategy?.preferredSource || providerSettings?.source || 'auto';
    return `Preferred ${sourceToken(preferred)}`;
}

export function providerStatusTags(descriptor, providerState) {
    void descriptor;
    const presentation = settingsPresentation(providerState);
    if (Array.isArray(presentation?.statusTags))
        return presentation.statusTags;

    return [];
}

export function providerStatusSummaryLabel(descriptor, providerState) {
    void descriptor;
    const presentation = settingsPresentation(providerState);
    if (presentation?.sourceStatusLabel)
        return presentation.sourceStatusLabel;
    return '';
}

export function providerFallbackLabel(providerState) {
    const presentation = settingsPresentation(providerState);
    if (presentation?.fallbackLabel)
        return presentation.fallbackLabel;
    return '';
}

export function providerSourceReason(providerSettings, providerState) {
    void providerSettings;
    const presentation = settingsPresentation(providerState);
    if (presentation?.sourceReasonLabel)
        return presentation.sourceReasonLabel;
    if (presentation?.fallbackLabel)
        return presentation.fallbackLabel;
    return '';
}

export function providerStrategyText(providerSettings, providerState) {
    const presentation = settingsPresentation(providerState);
    if (presentation?.strategyLabel)
        return presentation.strategyLabel;

    const sourceModel = providerState?.sourceModel;
    const strategy = sourceModel?.sourceStrategy;
    const preferred = strategy?.preferredSource || providerSettings?.source || 'auto';
    const resolved = strategy?.resolvedSource || sourceModel?.activeSource || preferred;
    return `Preferred ${sourceToken(preferred)} · Active ${sourceToken(resolved)}`;
}

export function providerAvailabilityText(descriptor, providerState) {
    void descriptor;
    const presentation = settingsPresentation(providerState);
    if (presentation?.availabilityLabel)
        return presentation.availabilityLabel;
    return 'Unknown';
}
