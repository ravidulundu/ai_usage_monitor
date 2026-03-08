import GObject from 'gi://GObject';
import St from 'gi://St';
import Clutter from 'gi://Clutter';
import GLib from 'gi://GLib';

import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

import {IndicatorActionsMixin} from './indicatorActionsMixin.js';
import {IndicatorContentFlowMixin} from './indicatorContentFlowMixin.js';
import {IndicatorHeaderMixin} from './indicatorHeaderMixin.js';
import {IndicatorLifecycleMixin} from './indicatorLifecycleMixin.js';
import {IndicatorPanelMixin} from './indicatorPanelMixin.js';
import {IndicatorSectionPrimitivesMixin} from './indicatorSectionPrimitivesMixin.js';
import {IndicatorSectionsMixin} from './indicatorSectionsMixin.js';
import {IndicatorTabsMixin} from './indicatorTabsMixin.js';
import {PANEL_RING_SIZE} from './popupLayoutTokens.js';

const AIUsageIndicator = GObject.registerClass(
class AIUsageIndicator extends PanelMenu.Button {
    _init(extensionPath, settings, extension) {
        super._init(0.0, 'AI Usage Monitor', false);

        this._extensionPath = extensionPath;
        this._settings = settings;
        this._extension = extension;
        this._destroyed = false;
        this._refreshGeneration = 0;
        this._timeoutId = null;
        this._cancellable = null;
        this._activeProcess = null;
        this._panelRingRepaintId = null;
        this._menuOpenStateChangedId = null;

        this._popupVm = {};
        this._popupTabs = [];
        this._popupSwitcherTabs = [];
        this._popupProviders = [];
        this._popupOverviewCards = [];
        this._popupSelectedProviderId = '';
        this._popupPanel = null;
        this._selectedPopupProvider = '';
        this._lastRenderedIdentityByProvider = {};
        this._identityMismatchByProvider = {};

        this._isLoading = true;
        this._lastError = '';
        this._panelPct = 0;
        this._panelTone = 'ok';
        this._toolGIcons = {};
        this._identityRefreshTimeoutId = null;

        const box = new St.BoxLayout({style_class: 'panel-status-menu-box'});
        this._panelToolIcon = new St.Icon({
            icon_size: 14,
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'ai-usage-panel-tool-icon',
        });
        this._panelToolFallback = new St.Label({
            text: '',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'ai-usage-panel-tool-fallback',
        });
        this._panelRing = new St.DrawingArea({
            width: PANEL_RING_SIZE,
            height: PANEL_RING_SIZE,
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'ai-usage-panel-ring',
        });
        this._panelRingRepaintId = this._panelRing.connect('repaint', this._drawPanelRing.bind(this));
        this._panelLabel = new St.Label({
            text: '...',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'ai-usage-panel-label',
        });

        box.add_child(this._panelToolIcon);
        box.add_child(this._panelToolFallback);
        box.add_child(this._panelRing);
        box.add_child(this._panelLabel);
        this.add_child(box);

        this._buildMenu();
        this._menuOpenStateChangedId = this.menu.connect('open-state-changed', (_menu, open) => {
            if (open) {
                this._updateContent();
                this._refresh();
                return;
            }
            this._clearIdentityRefreshTimeout();
            this._resetBoxChildren(this._contentBox);
            this._resetBoxChildren(this._switcherBox);
        });

        this._settingsChangedId = this._settings.connect('changed', this._onSettingsChanged.bind(this));

        this._refresh();
        this._scheduleRefresh();
    }

    _buildMenu() {
        this.menu.removeAll();
        this._switcherBox = new St.BoxLayout({vertical: false, style_class: 'ai-usage-switcher-box'});
        this.menu.box.add_child(this._switcherBox);

        this._contentBox = new St.BoxLayout({vertical: true, style_class: 'ai-usage-content-box'});
        this.menu.box.add_child(this._contentBox);
    }

    _onSettingsChanged(_settings, key) {
        if (key === 'refresh-interval')
            this._scheduleRefresh();
        this._updatePanelIcon();
        this._updateContent();
    }

    _clearRefreshTimeout() {
        if (!this._timeoutId)
            return;
        GLib.source_remove(this._timeoutId);
        this._timeoutId = null;
    }

    _clearIdentityRefreshTimeout() {
        if (!this._identityRefreshTimeoutId)
            return;
        GLib.source_remove(this._identityRefreshTimeoutId);
        this._identityRefreshTimeoutId = null;
    }

    destroy() {
        this._destroyed = true;
        this._refreshGeneration += 1;

        if (this._cancellable) {
            this._cancellable.cancel();
            this._cancellable = null;
        }

        if (this._activeProcess) {
            try {
                this._activeProcess.force_exit();
            } catch (_e) {
                // Ignore force-exit errors on teardown.
            }
            this._activeProcess = null;
        }

        this._clearIdentityRefreshTimeout();
        this._clearRefreshTimeout();

        if (this._settingsChangedId) {
            this._settings.disconnect(this._settingsChangedId);
            this._settingsChangedId = null;
        }
        if (this._menuOpenStateChangedId) {
            this._disconnectSignal(this.menu, this._menuOpenStateChangedId);
            this._menuOpenStateChangedId = null;
        }
        if (this._panelRingRepaintId) {
            this._disconnectSignal(this._panelRing, this._panelRingRepaintId);
            this._panelRingRepaintId = null;
        }

        this._toolGIcons = {};
        this._popupVm = {};
        this._popupTabs = [];
        this._popupSwitcherTabs = [];
        this._popupProviders = [];
        this._popupOverviewCards = [];
        this._identityMismatchByProvider = {};
        this._lastRenderedIdentityByProvider = {};

        super.destroy();
    }
});

Object.assign(
    AIUsageIndicator.prototype,
    IndicatorLifecycleMixin,
    IndicatorPanelMixin,
    IndicatorContentFlowMixin,
    IndicatorTabsMixin,
    IndicatorHeaderMixin,
    IndicatorSectionPrimitivesMixin,
    IndicatorSectionsMixin,
    IndicatorActionsMixin,
);

export default class AIUsageMonitorExtension extends Extension {
    enable() {
        this._indicator = new AIUsageIndicator(this.path, this.getSettings(), this);
        Main.panel.addToStatusArea(this.metadata.uuid, this._indicator);
    }

    disable() {
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
    }
}
