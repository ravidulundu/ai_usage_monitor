import GLib from 'gi://GLib';
import Gio from 'gi://Gio';

import {
    providerById as popupProviderById,
    providerTabs as popupProviderTabs,
    resolveSelectedProviderId as popupResolveSelectedProviderId,
} from './popupSelection.js';

export const IndicatorLifecycleMixin = {
    _scheduleRefresh() {
        this._clearRefreshTimeout();
        const interval = Math.max(20, this._settings.get_int('refresh-interval'));
        this._timeoutId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, interval, () => {
            this._refresh();
            return GLib.SOURCE_CONTINUE;
        });
    },

    _refresh() {
        if (this._destroyed)
            return;
        this._refreshGeneration += 1;
        const refreshGeneration = this._refreshGeneration;

        if (this._cancellable)
            this._cancellable.cancel();
        this._cancellable = new Gio.Cancellable();
        const cancellable = this._cancellable;

        this._isLoading = true;
        this._updatePanelIcon();

        let proc;
        try {
            const preferredProviderId = this._preferredPersistedProviderId();
            const argv = ['python3', `${this._extensionPath}/scripts/fetch_all_usage.py`, 'popup-vm'];
            if (preferredProviderId)
                argv.push(preferredProviderId);
            proc = new Gio.Subprocess({
                argv,
                flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            });
            proc.init(cancellable);
            this._activeProcess = proc;
        } catch (_e) {
            this._finalizeRefreshRequest(cancellable, proc);
            if (this._destroyed || refreshGeneration !== this._refreshGeneration)
                return;
            this._isLoading = false;
            this._lastError = 'Failed to start backend';
            this._setPopupData({});
            this._updatePanelIcon();
            this._updateContent();
            return;
        }

        proc.communicate_utf8_async(null, cancellable, (source, result) => {
            try {
                if (this._destroyed || refreshGeneration !== this._refreshGeneration)
                    return;
                const [, stdout, stderr] = source.communicate_utf8_finish(result);
                if (stdout?.trim()) {
                    this._setPopupData(JSON.parse(stdout.trim()));
                    this._lastError = '';
                } else {
                    this._setPopupData({});
                    this._lastError = stderr?.trim() || 'No output from backend';
                }
            } catch (e) {
                if (e.matches?.(Gio.IOErrorEnum, Gio.IOErrorEnum.CANCELLED))
                    return;
                this._setPopupData({});
                this._lastError = String(e?.message || e);
            } finally {
                this._finalizeRefreshRequest(cancellable, source);
            }

            this._isLoading = false;
            this._updatePanelIcon();
            if (this.menu?.isOpen)
                this._updateContent();
        });
    },

    _finalizeRefreshRequest(cancellable, process = null) {
        if (this._cancellable === cancellable)
            this._cancellable = null;
        if (!process || this._activeProcess === process)
            this._activeProcess = null;
    },

    _setPopupData(payload) {
        const popup = payload?.popup ?? {};
        this._popupVm = popup;
        this._popupTabs = Array.isArray(popup.tabs) ? popup.tabs : [];
        this._popupSwitcherTabs = Array.isArray(popup.switcherTabs)
            ? popup.switcherTabs
            : popupProviderTabs(this._popupTabs);
        const providers = Array.isArray(popup.providers) ? popup.providers : [];
        this._pruneIdentityCaches(providers);
        this._identityMismatchByProvider = this._buildIdentityMismatchMap(providers);
        this._popupProviders = providers;
        this._popupOverviewCards = Array.isArray(popup.overviewCards) ? popup.overviewCards : [];
        this._popupSelectedProviderId = popup.selectedProviderId || '';
        this._popupPanel = popup?.panel && typeof popup.panel === 'object' ? popup.panel : null;

        this._selectedPopupProvider = this._resolveSelectedProviderId(this._selectedPopupProvider);
        this._scheduleIdentityRefreshIfNeeded();
    },

    _pruneIdentityCaches(providers) {
        const keep = {};
        for (const provider of providers || []) {
            const providerId = provider?.id;
            if (providerId)
                keep[providerId] = true;
        }

        for (const providerId of Object.keys(this._lastRenderedIdentityByProvider || {})) {
            if (!keep[providerId])
                delete this._lastRenderedIdentityByProvider[providerId];
        }
        for (const providerId of Object.keys(this._identityMismatchByProvider || {})) {
            if (!keep[providerId])
                delete this._identityMismatchByProvider[providerId];
        }
    },

    _providerIdentityFingerprint(provider) {
        if (!provider)
            return '';
        if (provider.identityFingerprint)
            return String(provider.identityFingerprint);
        if (provider.identity?.fingerprint)
            return String(provider.identity.fingerprint);
        return '';
    },

    _buildIdentityMismatchMap(providers) {
        const mismatches = {};
        const snapshot = Array.isArray(providers) ? providers : [];
        for (const provider of snapshot) {
            const providerId = provider?.id;
            if (!providerId)
                continue;

            const nextFingerprint = this._providerIdentityFingerprint(provider);
            const previousFingerprint = this._lastRenderedIdentityByProvider[providerId] || '';
            const changed = previousFingerprint !== ''
                && nextFingerprint !== ''
                && previousFingerprint !== nextFingerprint;
            mismatches[providerId] = changed;

            if (nextFingerprint !== '')
                this._lastRenderedIdentityByProvider[providerId] = nextFingerprint;
        }
        return mismatches;
    },

    _identityRefreshPending() {
        if (this._popupVm?.identityRefreshPending === true)
            return true;
        if (this._popupProviders.some(provider =>
            provider?.identity?.changed === true || provider?.switchingState?.active === true
        )) {
            return true;
        }
        return Object.values(this._identityMismatchByProvider || {}).some(changed => changed === true);
    },

    _scheduleIdentityRefreshIfNeeded() {
        if (this._destroyed || !this.menu?.isOpen || !this._identityRefreshPending() || this._identityRefreshTimeoutId)
            return;

        this._identityRefreshTimeoutId = GLib.timeout_add(GLib.PRIORITY_DEFAULT, 300, () => {
            this._identityRefreshTimeoutId = null;
            this._refresh();
            return GLib.SOURCE_REMOVE;
        });
    },

    _clearRefreshTimeout() {
        if (!this._timeoutId)
            return;
        GLib.source_remove(this._timeoutId);
        this._timeoutId = null;
    },

    _clearIdentityRefreshTimeout() {
        if (!this._identityRefreshTimeoutId)
            return;
        GLib.source_remove(this._identityRefreshTimeoutId);
        this._identityRefreshTimeoutId = null;
    },

    _disconnectSignal(actor, signalId) {
        if (!actor || !signalId)
            return;
        try {
            actor.disconnect(signalId);
        } catch (_e) {
            // Ignore stale signal ids during teardown.
        }
    },

    _preferredPersistedProviderId() {
        const providerId = this._settings.get_string('panel-tool');
        if (!providerId || providerId === 'auto' || providerId === 'overview')
            return '';
        return providerId;
    },

    _providerById(providerId) {
        return popupProviderById(this._popupProviders, providerId);
    },

    _switcherTabs() {
        return Array.isArray(this._popupSwitcherTabs) ? this._popupSwitcherTabs : [];
    },

    _resolveSelectedProviderId(requestedId) {
        return popupResolveSelectedProviderId({
            requestedId,
            switcherTabs: this._switcherTabs(),
            popupSelectedProviderId: this._popupSelectedProviderId,
        });
    },

    _selectProvider(providerId) {
        this._selectedPopupProvider = this._resolveSelectedProviderId(providerId);
    },

    _getDisplayMode() {
        const mode = this._settings.get_int('panel-display-mode');
        return [0, 1, 2].includes(mode) ? mode : 0;
    },
};
