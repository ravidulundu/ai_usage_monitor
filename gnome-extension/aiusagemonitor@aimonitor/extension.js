import GLib from 'gi://GLib';
import GObject from 'gi://GObject';
import Gio from 'gi://Gio';
import St from 'gi://St';
import Clutter from 'gi://Clutter';
import Pango from 'gi://Pango';
import Cairo from 'cairo';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';

const PANEL_RING_SIZE = 16;
const PANEL_RING_STROKE = 2.2;
const POPUP_BAR_WIDTH = 150;

function menuItemActor(item) {
    return item.actor ?? item;
}

const AIUsageIndicator = GObject.registerClass(
class AIUsageIndicator extends PanelMenu.Button {
    _init(extensionPath, settings, extension) {
        super._init(0.0, 'AI Usage Monitor', false);

        this._extensionPath = extensionPath;
        this._settings = settings;
        this._extension = extension;
        this._timeoutId = null;
        this._cancellable = null;
        this._providerStates = [];
        this._isLoading = true;
        this._panelPct = 0;
        this._panelColor = '#22c55e';
        this._selectedPopupProvider = 'overview';
        this._toolGIcons = {};

        // Panel bar widgets
        let box = new St.BoxLayout({style_class: 'panel-status-menu-box'});

        this._panelToolIcon = new St.Icon({
            icon_size: 14,
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'ai-usage-panel-tool-icon',
        });

        this._panelToolFallback = new St.Label({
            text: 'AI',
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'ai-usage-panel-tool-fallback',
        });

        this._panelRing = new St.DrawingArea({
            width: PANEL_RING_SIZE,
            height: PANEL_RING_SIZE,
            y_align: Clutter.ActorAlign.CENTER,
            style_class: 'ai-usage-panel-ring',
        });
        this._panelRing.connect('repaint', this._drawPanelRing.bind(this));

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
        this.menu.connect('open-state-changed', (_menu, open) => {
            if (open)
                this._refresh();
        });

        this._settingsChangedId = this._settings.connect('changed', this._onSettingsChanged.bind(this));

        this._refresh();
        this._scheduleRefresh();
    }

    _buildMenu() {
        this.menu.removeAll();

        let headerBox = new St.BoxLayout({vertical: false, style_class: 'ai-usage-menu-header'});
        let headerLabel = new St.Label({
            text: 'AI Usage Monitor',
            style: 'font-weight: bold; font-size: 13px;',
        });
        headerBox.add_child(headerLabel);

        let refreshButton = new St.Button({
            style_class: 'button',
            child: new St.Icon({icon_name: 'view-refresh-symbolic', icon_size: 16}),
        });
        refreshButton.connect('clicked', () => this._refresh());

        let prefsButton = new St.Button({
            style_class: 'button',
            child: new St.Icon({icon_name: 'preferences-system-symbolic', icon_size: 16}),
        });
        prefsButton.connect('clicked', () => this._openPreferences());

        headerBox.add_child(new St.Label({text: ' ', x_expand: true}));
        headerBox.add_child(refreshButton);
        headerBox.add_child(prefsButton);

        this.menu.box.add_child(headerBox);
        this.menu.box.add_child(menuItemActor(new PopupMenu.PopupSeparatorMenuItem()));

        this._switcherBox = new St.BoxLayout({vertical: false, style_class: 'ai-usage-switcher-box'});
        this.menu.box.add_child(this._switcherBox);

        this._contentBox = new St.BoxLayout({vertical: true, style_class: 'ai-usage-content-box'});
        this.menu.box.add_child(this._contentBox);
    }

    _updatePanelIcon() {
        const selectedTool = this._settings.get_string('panel-tool');
        const mode = this._getDisplayMode();
        const provider = this._resolvePanelTool(selectedTool);
        let pct = this._clampPct(this._getToolPct(provider));

        if (this._isLoading)
            this._panelLabel.text = '...';
        else if (provider?.error)
            this._panelLabel.text = '!';
        else if (provider?.incident?.indicator && provider.incident.indicator !== 'none')
            this._panelLabel.text = '!';
        else
            this._panelLabel.text = `${Math.round(pct)}%`;

        let gicon = this._providerGIcon(provider);
        if (gicon) {
            this._panelToolIcon.gicon = gicon;
            this._panelToolIcon.visible = true;
            this._panelToolFallback.visible = false;
        } else {
            this._panelToolIcon.visible = false;
            this._panelToolFallback.text = this._providerBadgeText(provider);
            this._panelToolFallback.visible = !!provider;
            this._panelToolFallback.style = `font-size: 9px; font-weight: bold; color: ${this._providerBranding(provider).color || color}; min-width: 18px;`;
        }

        let color = this._getProviderColor(provider, pct);
        this._panelPct = pct;
        this._panelColor = color;
        this._panelRing.queue_repaint();
        this._panelLabel.style = `font-size: 11px; font-weight: bold; color: ${color};`;

        this._panelRing.visible = mode !== 2;
        this._panelLabel.visible = mode !== 1;

        let toolName = this._getToolName(provider);
        let resetTime = this._getToolReset(provider);
        let tooltipText = 'AI Usage Monitor';
        if (!this._isLoading && resetTime)
            tooltipText += `\n${toolName} · ${this._formatReset(resetTime)} until reset`;
        else if (!this._isLoading)
            tooltipText += `\n${toolName}`;
        if (!this._isLoading && provider?.incident?.indicator && provider.incident.indicator !== 'none')
            tooltipText += `\nStatus: ${provider.incident.description || provider.incident.indicator}`;

        this.accessible_name = tooltipText;
    }

    _openPreferences() {
        try {
            this._extension.openPreferences();
        } catch (_e) {}
    }

    _visibleProviders() {
        let providers = (this._providerStates || []).filter(provider => provider.enabled !== false && provider.installed === true);
        providers.sort((a, b) => this._providerRank(a) - this._providerRank(b));
        return providers;
    }

    _overviewProviders() {
        return this._visibleProviders().slice(0, 3);
    }

    _toolUsable(provider) {
        if (!provider?.installed || provider.error)
            return false;
        if (!provider.primaryMetric && !provider.secondaryMetric)
            return false;
        return true;
    }

    _resolvePanelTool(selectedTool) {
        let visible = this._visibleProviders();
        let preferred = visible.find(provider => provider.id === selectedTool);
        if (preferred)
            return preferred;
        return visible[0] ?? null;
    }

    _getToolPct(provider) {
        return Number(provider?.primaryMetric?.usedPct ?? 0);
    }

    _getToolReset(provider) {
        return provider?.primaryMetric?.resetAt ?? null;
    }

    _getToolName(provider) {
        return provider?.displayName ?? 'AI Usage Monitor';
    }

    _getDisplayMode() {
        let mode = this._settings.get_int('panel-display-mode');
        return [0, 1, 2].includes(mode) ? mode : 0;
    }

    _drawPanelRing(area) {
        let cr = area.get_context();
        try {
            let [width, height] = area.get_surface_size();
            let cx = width / 2;
            let cy = height / 2;
            let radius = Math.min(width, height) / 2 - PANEL_RING_STROKE;
            let start = -Math.PI / 2;
            let end = start + (Math.PI * 2 * (this._panelPct / 100));

            cr.setOperator(Cairo.Operator.CLEAR);
            cr.paint();
            cr.setOperator(Cairo.Operator.OVER);

            cr.setLineWidth(PANEL_RING_STROKE);
            cr.setSourceRGBA(1, 1, 1, 0.22);
            cr.arc(cx, cy, radius, 0, Math.PI * 2);
            cr.stroke();

            if (this._panelPct > 0) {
                let [r, g, b] = this._hexToRgb(this._panelColor);
                cr.setSourceRGBA(r, g, b, 1);
                cr.arc(cx, cy, radius, start, end);
                cr.stroke();
            }
        } finally {
            cr.$dispose();
        }
    }

    _updateContent() {
        this._updateSwitcher();
        this._contentBox.destroy_all_children();

        let visibleProviders = this._visibleProviders().filter(provider => provider.installed);
        let anyVisible = false;

        if (this._selectedPopupProvider !== 'overview') {
            let selected = visibleProviders.find(provider => provider.id === this._selectedPopupProvider);
            if (!selected)
                this._selectedPopupProvider = 'overview';
        }

        if (this._selectedPopupProvider === 'overview') {
            for (let provider of this._overviewProviders().filter(provider => provider.installed)) {
                this._contentBox.add_child(this._createToolSection(provider, true));
                anyVisible = true;
            }
        } else {
            let selected = visibleProviders.find(provider => provider.id === this._selectedPopupProvider);
            if (selected) {
                this._contentBox.add_child(this._createToolSection(selected, false));
                anyVisible = true;
            }
        }

        if (!anyVisible) {
            let msg = this._isLoading ? 'Loading...' :
                ((this._providerStates || []).length > 0)
                    ? 'All tools hidden in settings' : 'No AI tools detected';
            this._contentBox.add_child(new St.Label({
                text: msg,
                style: 'color: gray; text-align: center; padding: 20px;',
            }));
        }

        this.menu.box.queue_relayout();
    }

    _updateSwitcher() {
        if (!this._switcherBox)
            return;

        this._switcherBox.destroy_all_children();

        let visibleProviders = this._visibleProviders();
        if (visibleProviders.length === 0)
            return;

        this._switcherBox.add_child(this._createSwitcherButton('Overview', 'overview'));
        for (let provider of visibleProviders)
            this._switcherBox.add_child(this._createSwitcherButton(provider.displayName || provider.id, provider.id));
    }

    _createSwitcherButton(label, providerId) {
        let active = this._selectedPopupProvider === providerId;
        let button = new St.Button({
            label,
            style_class: active ? 'ai-usage-switcher-button active' : 'ai-usage-switcher-button',
            can_focus: true,
        });
        button.connect('clicked', () => {
            this._selectedPopupProvider = providerId;
            this._updateContent();
        });
        return button;
    }

    _createToolSection(provider, compact = false) {
        let section = new St.BoxLayout({
            vertical: true,
            style_class: compact ? 'ai-usage-provider-card compact' : 'ai-usage-provider-card',
        });

        let headerBox = new St.BoxLayout({vertical: false, style_class: 'ai-usage-provider-header'});

        let gicon = this._providerGIcon(provider);
        let assetName = this._providerAssetName(provider);
        if (gicon) {
            try {
                let icon = new St.Icon({
                    gicon,
                    icon_size: 18,
                    style_class: 'ai-usage-provider-icon',
                });
                headerBox.add_child(icon);
            } catch (_e) {}
        } else {
            headerBox.add_child(new St.Label({
                text: this._providerBadgeText(provider),
                style_class: 'ai-usage-provider-badge',
                style: `background: ${this._providerBranding(provider).color || '#64748b'};`,
            }));
        }

        headerBox.add_child(new St.Label({
            text: (provider.displayName || provider.id || '').toUpperCase(),
            style_class: 'ai-usage-provider-title',
        }));

        let subtitle = this._providerSubtitle(provider);
        if (subtitle) {
            headerBox.add_child(new St.Label({
                text: ` · ${subtitle}`,
                style_class: 'ai-usage-provider-subtitle',
            }));
        }
        section.add_child(headerBox);

        if (provider.error) {
            let errorLabel = new St.Label({
                text: provider.error,
                style_class: 'ai-usage-error',
            });
            errorLabel.clutter_text.line_wrap = true;
            errorLabel.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
            errorLabel.clutter_text.ellipsize = Pango.EllipsizeMode.NONE;
            section.add_child(errorLabel);
        }

        if (provider.incident?.indicator && provider.incident.indicator !== 'none') {
            let incidentLabel = new St.Label({
                text: `Status: ${provider.incident.description || provider.incident.indicator}`,
                style_class: 'ai-usage-muted-row',
            });
            incidentLabel.clutter_text.line_wrap = true;
            incidentLabel.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
            incidentLabel.clutter_text.ellipsize = Pango.EllipsizeMode.NONE;
            section.add_child(incidentLabel);
        }

        if (provider.primaryMetric && !provider.error)
            section.add_child(this._createUsageBar(provider.primaryMetric.label, provider.primaryMetric.usedPct, provider.primaryMetric.resetAt, compact));
        if (provider.secondaryMetric && !provider.error && !compact)
            section.add_child(this._createUsageBar(provider.secondaryMetric.label, provider.secondaryMetric.usedPct, provider.secondaryMetric.resetAt, compact));

        let buckets = provider.extras?.buckets ?? [];
        if (!provider.error && !compact) {
            for (let bucket of buckets)
                section.add_child(this._createUsageBar(bucket.model || 'Model', bucket.used_pct, bucket.reset_time, true));
        }

        if (!provider.error && !provider.primaryMetric && provider.installed) {
            section.add_child(new St.Label({
                text: 'No usage data yet',
                style_class: 'ai-usage-muted-row',
            }));
        }

        let usageSummary = this._formatLocalUsage(provider.localUsage);
        if (usageSummary && (!compact || !(provider.primaryMetric || provider.secondaryMetric))) {
            section.add_child(new St.Label({
                text: usageSummary,
                style_class: 'ai-usage-muted-row',
            }));
        }
        return section;
    }

    _createUsageBar(label, pct, resetTime, compact = false) {
        pct = this._clampPct(Number(pct ?? 0));
        let color = this._getUsageColor(pct);

        let box = new St.BoxLayout({
            vertical: false,
            style_class: compact ? 'ai-usage-bar-container compact' : 'ai-usage-bar-container',
        });

        box.add_child(new St.Label({
            text: label,
            style_class: compact ? 'ai-usage-bar-label compact' : 'ai-usage-bar-label',
        }));

        let barArea = new St.DrawingArea({
            width: POPUP_BAR_WIDTH,
            height: compact ? 6 : 8,
            y_align: Clutter.ActorAlign.CENTER,
        });
        barArea.connect('repaint', () => {
            let cr = barArea.get_context();
            try {
                let [w, h] = barArea.get_surface_size();
                let r = 3;
                let fill = Math.round((pct / 100) * w);

                cr.setOperator(Cairo.Operator.CLEAR);
                cr.paint();
                cr.setOperator(Cairo.Operator.OVER);

                cr.setSourceRGBA(1, 1, 1, 0.12);
                cr.newPath();
                cr.arc(r, r, r, Math.PI, Math.PI * 1.5);
                cr.arc(w - r, r, r, Math.PI * 1.5, 0);
                cr.arc(w - r, h - r, r, 0, Math.PI * 0.5);
                cr.arc(r, h - r, r, Math.PI * 0.5, Math.PI);
                cr.closePath();
                cr.fill();

                if (fill > 0) {
                    let [rr, g, b] = this._hexToRgb(color);
                    cr.setSourceRGBA(rr, g, b, 1);
                    cr.rectangle(0, 0, fill, h);
                    cr.fill();
                }
            } finally {
                cr.$dispose();
            }
        });
        box.add_child(barArea);

        box.add_child(new St.Label({
            text: ` ${Math.round(pct)}%`,
            style_class: compact ? 'ai-usage-bar-value compact' : 'ai-usage-bar-value',
            style: `color: ${color};`,
        }));

        if (resetTime) {
            box.add_child(new St.Label({
                text: this._formatReset(resetTime),
                style_class: compact ? 'ai-usage-bar-reset compact' : 'ai-usage-bar-reset',
            }));
        }

        return box;
    }

    _clampPct(value) {
        if (!Number.isFinite(value))
            return 0;
        return Math.max(0, Math.min(100, value));
    }

    _hexToRgb(hex) {
        let match = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        if (!match)
            return [1, 1, 1];
        return [
            parseInt(match[1], 16) / 255,
            parseInt(match[2], 16) / 255,
            parseInt(match[3], 16) / 255,
        ];
    }

    _getUsageColor(pct) {
        if (pct >= 90) return '#ef4444';
        if (pct >= 70) return '#f97316';
        if (pct >= 40) return '#eab308';
        return '#22c55e';
    }

    _getProviderColor(provider, pct) {
        if (provider?.error)
            return '#ef4444';
        let indicator = provider?.incident?.indicator;
        if (indicator === 'critical')
            return '#ef4444';
        if (indicator === 'major')
            return '#f97316';
        if (indicator === 'minor')
            return '#eab308';
        if (indicator === 'maintenance')
            return '#38bdf8';
        return this._getUsageColor(pct);
    }

    _formatReset(isoStr) {
        if (!isoStr) return '';
        let diff = new Date(isoStr) - new Date();
        if (diff <= 0) return 'soon';
        let hrs = Math.floor(diff / 3600000);
        let mins = Math.floor((diff % 3600000) / 60000);
        if (hrs >= 24)
            return `in ${Math.floor(hrs / 24)}d ${hrs % 24}h`;
        if (hrs > 0)
            return `in ${hrs}h ${mins}m`;
        return `in ${mins}m`;
    }

    _providerSubtitle(provider) {
        let extras = provider?.extras ?? {};
        let parts = [];
        if (provider?.source)
            parts.push(String(provider.source).toUpperCase());
        if (extras.model && extras.model !== 'local-cli')
            parts.push(extras.model);
        if (extras.plan && !(provider?.source === 'cli' && (extras.plan === 'api' || extras.plan === 'oauth')))
            parts.push(extras.plan);
        return parts.join(' · ');
    }

    _providerBadgeText(provider) {
        let branding = this._providerBranding(provider);
        if (branding.badgeText)
            return branding.badgeText;
        if (!provider?.displayName)
            return 'AI';
        let words = provider.displayName.split(/\s+/).filter(Boolean);
        if (words.length >= 2)
            return `${words[0][0]}${words[1][0]}`.toUpperCase();
        return provider.displayName.slice(0, 2).toUpperCase();
    }

    _providerBranding(provider) {
        return provider?.metadata?.branding ?? {};
    }

    _providerAssetName(provider) {
        let branding = this._providerBranding(provider);
        if (branding.assetName)
            return branding.assetName;
        if (branding.iconKey)
            return `${branding.iconKey}.svg`;
        return '';
    }

    _providerGIcon(provider) {
        let assetName = this._providerAssetName(provider);
        if (!assetName)
            return null;
        if (!this._toolGIcons[assetName]) {
            try {
                this._toolGIcons[assetName] = Gio.icon_new_for_string(`${this._extensionPath}/images/${assetName}`);
            } catch (_e) {
                this._toolGIcons[assetName] = null;
            }
        }
        return this._toolGIcons[assetName];
    }

    _providerRank(provider) {
        if ((provider?.primaryMetric || provider?.secondaryMetric) && !provider?.error)
            return 0;
        if (!provider?.error)
            return 1;
        return 2;
    }

    _formatLocalUsage(localUsage) {
        if (!localUsage)
            return '';
        let parts = [];
        if (localUsage.sessionTokens !== null && localUsage.sessionTokens !== undefined)
            parts.push(`session ${localUsage.sessionTokens} tok`);
        if (localUsage.last30DaysTokens !== null && localUsage.last30DaysTokens !== undefined)
            parts.push(`30d ${localUsage.last30DaysTokens} tok`);
        return parts.join(' · ');
    }

    _refresh() {
        if (this._cancellable)
            this._cancellable.cancel();
        this._cancellable = new Gio.Cancellable();

        this._isLoading = true;
        this._updatePanelIcon();

        let proc;
        try {
            proc = new Gio.Subprocess({
                argv: ['python3', `${this._extensionPath}/scripts/fetch_all_usage.py`],
                flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
            });
            proc.init(this._cancellable);
        } catch (e) {
            this._isLoading = false;
            this._updatePanelIcon();
            this._updateContent();
            return;
        }

        proc.communicate_utf8_async(null, this._cancellable, (source, result) => {
            try {
                let [, stdout] = source.communicate_utf8_finish(result);
                if (stdout?.trim()) {
                    let parsed = JSON.parse(stdout.trim());
                    this._providerStates = parsed.providers || [];
                }
            } catch (e) {
                if (e.matches(Gio.IOErrorEnum, Gio.IOErrorEnum.CANCELLED))
                    return;
            }

            this._isLoading = false;
            this._updatePanelIcon();
            this._updateContent();
        });
    }

    _scheduleRefresh() {
        if (this._timeoutId)
            GLib.source_remove(this._timeoutId);

        let interval = this._settings.get_int('refresh-interval');
        this._timeoutId = GLib.timeout_add_seconds(GLib.PRIORITY_DEFAULT, interval, () => {
            this._refresh();
            return GLib.SOURCE_CONTINUE;
        });
    }

    _onSettingsChanged(_settings, key) {
        if (key === 'refresh-interval')
            this._scheduleRefresh();
        this._updatePanelIcon();
        this._updateContent();
    }

    destroy() {
        if (this._cancellable) {
            this._cancellable.cancel();
            this._cancellable = null;
        }

        if (this._timeoutId) {
            GLib.source_remove(this._timeoutId);
            this._timeoutId = null;
        }

        if (this._settingsChangedId) {
            this._settings.disconnect(this._settingsChangedId);
            this._settingsChangedId = null;
        }

        super.destroy();
    }
});

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
