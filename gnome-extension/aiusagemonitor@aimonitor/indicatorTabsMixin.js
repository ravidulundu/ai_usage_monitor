import St from 'gi://St';
import Cairo from 'cairo';

import {POPUP_TOKENS} from './popupLayoutTokens.js';

export const IndicatorTabsMixin = {
    buildProviderTabsRow() {
        const row = new St.BoxLayout({
            vertical: false,
            style_class: 'ai-usage-switcher-row ai-usage-tabs-row',
        });

        for (const spec of this._switcherTabs())
            row.add_child(this._buildProviderTabButton(spec));

        return row;
    },

    _buildProviderTabButton(tab) {
        const isActive = this._selectedPopupProvider === tab.id;
        const button = new St.Button({
            style_class: isActive
                ? 'ai-usage-switcher-button ai-usage-tab-button active'
                : 'ai-usage-switcher-button ai-usage-tab-button',
            reactive: true,
            can_focus: true,
        });
        button.set_child(this._buildProviderTabButtonContent(tab, isActive));
        button.connect('clicked', () => {
            this._selectProvider(tab.id);
            this._updateContent();
        });
        return button;
    },

    _buildProviderTabButtonContent(tab, isActive) {
        const isOverview = tab.kind === 'overview';
        const content = new St.BoxLayout({
            vertical: true,
            style_class: 'ai-usage-tab-content ai-usage-provider-tab-content',
        });
        const top = new St.BoxLayout({
            vertical: false,
            style_class: 'ai-usage-tab-top ai-usage-provider-tab-top',
        });

        const icon = !isOverview && tab?.iconKey ? this._providerGIconByIconKey(tab.iconKey) : null;
        if (isOverview) {
            top.add_child(new St.Icon({
                icon_name: 'view-grid-symbolic',
                icon_size: 13,
                style_class: 'ai-usage-tab-icon',
            }));
        } else if (icon) {
            top.add_child(new St.Icon({gicon: icon, icon_size: 13, style_class: 'ai-usage-tab-icon'}));
        } else {
            top.add_child(new St.Label({text: tab?.badgeText || '', style_class: 'ai-usage-tab-badge'}));
        }

        top.add_child(new St.Label({
            text: tab?.shortTitle || tab?.title || tab?.id || '',
            style_class: 'ai-usage-tab-label',
        }));

        content.add_child(top);
        content.add_child(this._buildMiniMetricLine(tab, isActive, true));
        return content;
    },

    _buildMiniMetricLine(tab, isActive, isSelectable = true) {
        const area = new St.DrawingArea({
            width: 48,
            height: Math.max(2, Math.floor(POPUP_TOKENS.progressThickness / 2)),
            style_class: isActive && isSelectable
                ? 'ai-usage-tab-mini-line tone-accent'
                : `ai-usage-tab-mini-line ${isSelectable ? 'tone-muted' : 'tone-disabled'}`,
        });

        area.connect('repaint', () => {
            const cr = area.get_context();
            try {
                const [w, h] = area.get_surface_size();
                const miniMetric = tab?.miniMetric ?? {};
                const mode = isSelectable ? (miniMetric.mode || 'none') : 'none';

                let pct = 0;
                if (mode === 'percent' && Number.isFinite(Number(miniMetric.percent)))
                    pct = this._clampPct(Number(miniMetric.percent));
                else if (mode === 'tick')
                    pct = 12;
                else if (isActive && isSelectable)
                    pct = 100;

                const fillWidth = Math.max(0, Math.min(w, Math.round((pct / 100) * w)));

                cr.setOperator(Cairo.Operator.CLEAR);
                cr.paint();
                cr.setOperator(Cairo.Operator.OVER);

                const [tr, tg, tb, ta] = this._actorForegroundRgba(area, POPUP_TOKENS.separatorOpacity + 0.05);
                cr.setSourceRGBA(tr, tg, tb, ta);
                cr.rectangle(0, 0, w, h);
                cr.fill();

                if (fillWidth > 0) {
                    const [fr, fg, fb, fa] = this._actorForegroundRgba(area, isActive ? 1 : 0.85);
                    cr.setSourceRGBA(fr, fg, fb, fa);
                    cr.rectangle(0, 0, fillWidth, h);
                    cr.fill();
                }
            } finally {
                cr.$dispose();
            }
        });

        return area;
    },
};
