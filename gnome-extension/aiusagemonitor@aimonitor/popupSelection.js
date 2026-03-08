/**
 * Return visible and enabled popup tabs from VM payload.
 *
 * @param {Array<object>} popupTabs
 * @returns {Array<object>}
 */
export function providerTabs(popupTabs) {
    return (Array.isArray(popupTabs) ? popupTabs : []).filter(tab =>
        tab
        && tab.kind === 'provider'
        && tab.visible !== false
        && tab.enabled !== false
    );
}

/**
 * Find provider VM by id.
 *
 * @param {Array<object>} popupProviders
 * @param {string} providerId
 * @returns {object | null}
 */
export function providerById(popupProviders, providerId) {
    return (Array.isArray(popupProviders) ? popupProviders : []).find(provider => provider?.id === providerId) ?? null;
}

function _selectableTabs(switcherTabs) {
    return (Array.isArray(switcherTabs) ? switcherTabs : []).filter(tab =>
        tab
        && tab.visible !== false
        && tab.enabled !== false
    );
}

/**
 * Resolve selected tab id from VM-backed switcher tabs.
 *
 * @param {object} args
 * @param {string} args.requestedId
 * @param {Array<object>} args.switcherTabs
 * @param {string} args.popupSelectedProviderId
 * @returns {string}
 */
export function resolveSelectedProviderId({
    requestedId,
    switcherTabs,
    popupSelectedProviderId,
}) {
    const tabs = _selectableTabs(switcherTabs);
    if (tabs.length === 0)
        return '';

    if (requestedId && tabs.some(tab => tab.id === requestedId))
        return requestedId;

    if (popupSelectedProviderId && tabs.some(tab => tab.id === popupSelectedProviderId))
        return popupSelectedProviderId;

    const firstProvider = tabs.find(tab => tab.kind === 'provider');
    if (firstProvider)
        return firstProvider.id;

    return tabs[0]?.id || '';
}
