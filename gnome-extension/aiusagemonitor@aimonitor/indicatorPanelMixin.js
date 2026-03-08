import Gio from 'gi://Gio';
import Cairo from 'cairo';

import {PANEL_RING_STROKE} from './popupLayoutTokens.js';

export const IndicatorPanelMixin = {
    _updatePanelIcon() {
        const mode = this._getDisplayMode();
        const panel = this._popupPanel && typeof this._popupPanel === 'object'
            ? this._popupPanel
            : {};
        const provider = panel.providerId ? this._providerById(panel.providerId) : null;
        const pct = Number.isFinite(Number(panel.percent))
            ? this._clampPct(Number(panel.percent))
            : null;
        const tone = panel.tone || 'ok';

        if (this._isLoading)
            this._panelLabel.text = '...';
        else
            this._panelLabel.text = panel.displayText || '-';

        const gicon = panel.iconKey ? this._providerGIconByIconKey(panel.iconKey) : null;
        if (gicon) {
            this._panelToolIcon.gicon = gicon;
            this._panelToolIcon.visible = true;
            this._panelToolFallback.visible = false;
        } else {
            this._panelToolIcon.visible = false;
            this._panelToolFallback.text = panel.badgeText ?? '';
            this._panelToolFallback.visible = !this._isLoading && !!this._panelToolFallback.text;
        }

        this._panelPct = pct === null ? 0 : pct;
        this._panelTone = tone;
        this._applyToneClass(this._panelLabel, tone);
        this._applyToneClass(this._panelToolFallback, tone);
        this._panelRing.queue_repaint();

        this._panelRing.visible = mode !== 2;
        this._panelLabel.visible = mode !== 1;

        let tooltipText = 'AI Usage Monitor';
        const tooltipLines = Array.isArray(panel.tooltipLines)
            ? panel.tooltipLines.filter(line => typeof line === 'string' && line.trim() !== '')
            : [];
        if (!this._isLoading && tooltipLines.length > 0)
            tooltipText += `\n${tooltipLines.join('\n')}`;
        else if (!this._isLoading && provider?.displayName)
            tooltipText += `\n${provider.displayName}`;

        this.accessible_name = tooltipText;
    },

    _drawPanelRing(area) {
        const cr = area.get_context();
        try {
            const [width, height] = area.get_surface_size();
            const cx = width / 2;
            const cy = height / 2;
            const radius = Math.min(width, height) / 2 - PANEL_RING_STROKE;
            const start = -Math.PI / 2;
            const end = start + (Math.PI * 2 * (this._panelPct / 100));

            cr.setOperator(Cairo.Operator.CLEAR);
            cr.paint();
            cr.setOperator(Cairo.Operator.OVER);

            cr.setLineWidth(PANEL_RING_STROKE);
            const [trackR, trackG, trackB, trackA] = this._actorForegroundRgba(this._panelLabel, 0.22);
            cr.setSourceRGBA(trackR, trackG, trackB, trackA);
            cr.arc(cx, cy, radius, 0, Math.PI * 2);
            cr.stroke();

            if (this._panelPct > 0) {
                const [r, g, b, a] = this._actorForegroundRgba(this._panelLabel, 1);
                cr.setSourceRGBA(r, g, b, a);
                cr.arc(cx, cy, radius, start, end);
                cr.stroke();
            }
        } finally {
            cr.$dispose();
        }
    },

    _providerGIconByIconKey(iconKey) {
        if (!iconKey)
            return null;
        const assetName = `${iconKey}.svg`;
        if (!this._toolGIcons[assetName]) {
            try {
                this._toolGIcons[assetName] = Gio.icon_new_for_string(`${this._extensionPath}/images/${assetName}`);
            } catch (_e) {
                this._toolGIcons[assetName] = null;
            }
        }
        return this._toolGIcons[assetName];
    },

    _clampPct(value) {
        if (!Number.isFinite(value))
            return 0;
        return Math.max(0, Math.min(100, value));
    },

    _applyToneClass(actor, tone) {
        if (!actor)
            return;
        for (const toneClass of ['ai-tone-ok', 'ai-tone-accent', 'ai-tone-warn', 'ai-tone-error'])
            actor.remove_style_class_name(toneClass);
        actor.add_style_class_name(`ai-tone-${tone}`);
    },

    _actorForegroundRgba(actor, alpha = 1) {
        try {
            const node = actor?.get_theme_node?.();
            const color = node?.get_foreground_color?.();
            if (color) {
                return [
                    color.red / 255,
                    color.green / 255,
                    color.blue / 255,
                    Math.max(0, Math.min(1, alpha)),
                ];
            }
        } catch (_e) {
            // Ignore and fallback to neutral color.
        }
        return [1, 1, 1, Math.max(0, Math.min(1, alpha))];
    },
};
