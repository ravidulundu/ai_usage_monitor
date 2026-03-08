import Gio from 'gi://Gio';

export const IndicatorActionsMixin = {
    _iconNameForAction(actionId) {
        switch (actionId) {
        case 'usage_dashboard':
            return 'view-statistics-symbolic';
        case 'status_page':
            return 'network-workgroup-symbolic';
        case 'settings':
            return 'settings-symbolic';
        case 'about':
            return 'help-about-symbolic';
        case 'quit':
            return 'window-close-symbolic';
        default:
            return 'go-next-symbolic';
        }
    },

    _dispatchAction(action) {
        if (!action || action.enabled !== true || !this._isActionSupported(action))
            return;

        switch (action.intent) {
        case 'open_url':
            if (action.target)
                this._openUrl(action.target);
            break;
        case 'open_settings':
            this._openPreferences();
            break;
        case 'about':
            if (action.target)
                this._openUrl(action.target);
            break;
        case 'quit':
            this._quitHost();
            break;
        default:
            break;
        }
    },

    _isActionSupported(action) {
        if (!action)
            return false;
        switch (action.intent) {
        case 'open_url':
            return this._canOpenUrl();
        case 'open_settings':
            return typeof this._extension?.openPreferences === 'function';
        case 'about':
            return this._canOpenUrl() && !!action.target;
        case 'quit':
            return this._canQuitHost();
        default:
            return true;
        }
    },

    _canOpenUrl() {
        return typeof Gio.app_info_launch_default_for_uri === 'function';
    },

    _canQuitHost() {
        return false;
    },

    _quitHost() {
        if (!this._canQuitHost())
            return;
        this.menu.close();
    },

    _openPreferences() {
        try {
            this._extension.openPreferences();
        } catch (_e) {
            // Ignore: shell may reject opening prefs in some contexts.
        }
    },

    _openUrl(url) {
        try {
            Gio.app_info_launch_default_for_uri(url, global.create_app_launch_context(0, -1));
        } catch (_e) {
            // Ignore: we surface action availability separately.
        }
    },
};
