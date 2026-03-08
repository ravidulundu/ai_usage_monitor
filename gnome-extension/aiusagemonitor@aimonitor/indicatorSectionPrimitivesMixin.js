import Clutter from 'gi://Clutter';
import St from 'gi://St';
import Cairo from 'cairo';

import {POPUP_BAR_WIDTH, POPUP_TOKENS} from './popupLayoutTokens.js';

export const IndicatorSectionPrimitivesMixin = {
    _buildProgressLine(percentValue, available = true, tone = 'accent') {
        const area = new St.DrawingArea({
            width: POPUP_BAR_WIDTH,
            height: POPUP_TOKENS.progressThickness,
            x_expand: true,
            style_class: `ai-usage-progress-line tone-${available ? tone : 'muted'}`,
        });

        area.connect('repaint', () => {
            const cr = area.get_context();
            try {
                const [w, h] = area.get_surface_size();
                const pct = Number.isFinite(Number(percentValue)) ? this._clampPct(Number(percentValue)) : null;
                const fill = pct === null ? 0 : Math.round((pct / 100) * w);
                const radius = h / 2;

                cr.setOperator(Cairo.Operator.CLEAR);
                cr.paint();
                cr.setOperator(Cairo.Operator.OVER);

                const [tr, tg, tb, ta] = this._actorForegroundRgba(area, POPUP_TOKENS.separatorOpacity + 0.03);
                cr.setSourceRGBA(tr, tg, tb, ta);
                cr.newPath();
                cr.arc(radius, radius, radius, Math.PI, Math.PI * 1.5);
                cr.arc(w - radius, radius, radius, Math.PI * 1.5, 0);
                cr.arc(w - radius, h - radius, radius, 0, Math.PI * 0.5);
                cr.arc(radius, h - radius, radius, Math.PI * 0.5, Math.PI);
                cr.closePath();
                cr.fill();

                if (fill > 0) {
                    const [fr, fg, fb, fa] = this._actorForegroundRgba(area, available ? 1 : 0.45);
                    cr.setSourceRGBA(fr, fg, fb, fa);
                    cr.rectangle(0, 0, fill, h);
                    cr.fill();
                }
            } finally {
                cr.$dispose();
            }
        });

        return area;
    },

    _buildDataRow(rowData) {
        const row = new St.BoxLayout({vertical: true, style_class: 'ai-usage-data-row'});
        const valueRow = new St.BoxLayout({vertical: false, style_class: 'ai-usage-data-value-row'});

        if (rowData?.label) {
            valueRow.add_child(new St.Label({text: rowData.label, style_class: 'ai-usage-data-value'}));
            valueRow.add_child(new St.Widget({x_expand: true}));
        }

        valueRow.add_child(new St.Label({text: rowData?.value || '', style_class: 'ai-usage-data-value'}));
        row.add_child(valueRow);

        if (rowData?.meta)
            row.add_child(new St.Label({text: rowData.meta, style_class: 'ai-usage-data-meta'}));

        return row;
    },

    _buildDivider() {
        return new St.Widget({style_class: 'ai-usage-section-divider', x_expand: true, height: 1});
    },

    _buildDataSection(dataBlock, sectionClassName) {
        if (!dataBlock?.visible)
            return null;

        const section = new St.BoxLayout({vertical: true, style_class: sectionClassName});
        section.add_child(new St.Label({text: dataBlock.title || '', style_class: 'ai-usage-block-title'}));

        for (const row of dataBlock.rows || [])
            section.add_child(this._buildDataRow(row));

        return section;
    },

    _buildActionRowContent(action) {
        const row = new St.BoxLayout({
            vertical: false,
            style_class: 'ai-usage-action-row',
            x_expand: true,
        });

        row.add_child(new St.Icon({
            icon_name: this._iconNameForAction(action.id),
            icon_size: 13,
            style_class: 'ai-usage-action-icon',
        }));

        row.add_child(new St.Label({
            text: action.label,
            style_class: 'ai-usage-action-label',
            x_expand: true,
        }));

        return row;
    },

    _buildOverviewCard(card) {
        const button = new St.Button({can_focus: true, style_class: 'ai-usage-overview-button'});
        const content = new St.BoxLayout({vertical: true, style_class: 'ai-usage-overview-card'});
        const header = new St.BoxLayout({vertical: false, style_class: 'ai-usage-overview-header'});

        header.add_child(new St.Label({text: card.title || '', style_class: 'ai-usage-overview-title'}));

        if (card.planLabel) {
            header.add_child(new St.Label({
                text: card.planLabel,
                style_class: 'ai-usage-overview-plan',
                x_align: Clutter.ActorAlign.END,
                x_expand: true,
            }));
        }

        content.add_child(header);
        for (const metric of card.metrics || [])
            content.add_child(this._buildOverviewMetricRow(metric));

        button.set_child(content);
        return button;
    },

    _buildOverviewMetricRow(metric) {
        const metricRow = new St.BoxLayout({vertical: false, style_class: 'ai-usage-overview-metric-row'});
        metricRow.add_child(new St.Label({text: metric.label || '', style_class: 'ai-usage-overview-metric-label'}));

        metricRow.add_child(this._buildProgressLine(
            metric.available === true ? metric.percent : null,
            metric.available === true,
            metric.tone || 'accent'
        ));

        metricRow.add_child(new St.Label({
            text: metric.displayText || '—',
            style_class: 'ai-usage-overview-metric-value',
        }));

        return metricRow;
    },

    _metricRowClass(metric) {
        const tone = metric?.tone || 'accent';
        if (tone === 'error')
            return 'ai-usage-metric-row tone-error';
        if (tone === 'warn')
            return 'ai-usage-metric-row tone-warn';
        return 'ai-usage-metric-row';
    },
};
