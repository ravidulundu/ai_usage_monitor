import Clutter from 'gi://Clutter';
import Pango from 'gi://Pango';
import St from 'gi://St';

export const IndicatorSectionsMixin = {
    buildMetricsSection(provider) {
        const metrics = Array.isArray(provider?.metrics) ? provider.metrics : [];
        if (metrics.length === 0)
            return null;

        const section = new St.BoxLayout({vertical: true, style_class: 'ai-usage-metrics-section'});
        for (let i = 0; i < metrics.length; i++) {
            section.add_child(this.buildMetricRow(metrics[i]));
            if (i < metrics.length - 1)
                section.add_child(this._buildDivider());
        }

        return section;
    },

    buildMetricRow(metric) {
        const row = new St.BoxLayout({vertical: true, style_class: this._metricRowClass(metric)});
        row.add_child(new St.Label({text: metric?.label || '', style_class: 'ai-usage-metric-title'}));
        row.add_child(this._buildProgressLine(metric.percent, metric.available === true, metric?.tone || 'accent'));

        const meta = new St.BoxLayout({vertical: false, style_class: 'ai-usage-metric-meta-row'});
        meta.add_child(new St.Label({text: metric?.leftText || '', style_class: 'ai-usage-metric-left'}));
        meta.add_child(new St.Label({
            text: metric?.rightText || '',
            style_class: 'ai-usage-metric-right',
            x_align: Clutter.ActorAlign.END,
            x_expand: true,
        }));
        row.add_child(meta);

        if (metric.secondaryText) {
            const secondary = new St.Label({text: metric.secondaryText, style_class: 'ai-usage-metric-secondary'});
            secondary.clutter_text.line_wrap = true;
            secondary.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
            secondary.clutter_text.ellipsize = Pango.EllipsizeMode.NONE;
            row.add_child(secondary);
        }

        return row;
    },

    buildExtraUsageSection(provider) {
        return this._buildDataSection(provider?.extraUsage, 'ai-usage-extra-usage-section');
    },

    buildCostSection(provider) {
        return this._buildDataSection(provider?.cost, 'ai-usage-cost-section');
    },

    buildActionList(provider) {
        const actions = (provider?.actions || []).filter(action => action?.visible === true && this._isActionSupported(action));
        if (actions.length === 0)
            return null;

        const section = new St.BoxLayout({vertical: true, style_class: 'ai-usage-actions-section'});
        section.add_child(new St.Label({text: 'Actions', style_class: 'ai-usage-block-title'}));

        const list = new St.BoxLayout({vertical: true, style_class: 'ai-usage-action-list'});
        for (const action of actions) {
            const button = new St.Button({
                can_focus: true,
                reactive: action.enabled === true,
                style_class: action.enabled === true
                    ? 'ai-usage-action-button'
                    : 'ai-usage-action-button disabled',
            });
            button.set_child(this._buildActionRowContent(action));
            button.connect('clicked', () => this._dispatchAction(action));
            list.add_child(button);
        }

        section.add_child(list);
        return section;
    },

    _providerDetailBlocks(provider, forceSwitching) {
        const blocks = [this.buildHeaderSection(provider)];
        if (forceSwitching) {
            blocks.push(this.buildSwitchingStateSection(provider, true));
        } else {
            blocks.push(this.buildMetricsSection(provider));
            blocks.push(this.buildExtraUsageSection(provider));
            blocks.push(this.buildCostSection(provider));
        }
        blocks.push(this.buildActionList(provider));
        return blocks;
    },

    buildProviderDetailSection(provider) {
        const section = new St.BoxLayout({vertical: true, style_class: 'ai-usage-provider-detail-section'});
        const identityMismatch = provider?.id
            ? this._identityMismatchByProvider?.[provider.id] === true
            : false;
        const forceSwitching = provider?.switchingState?.active === true || identityMismatch;

        let hasAny = false;
        const appendBlock = block => {
            if (!block)
                return;
            if (hasAny)
                section.add_child(this._buildDivider());
            section.add_child(block);
            hasAny = true;
        };

        for (const block of this._providerDetailBlocks(provider, forceSwitching))
            appendBlock(block);

        if (!hasAny)
            return this.buildEmptyState();
        return section;
    },

    buildOverviewCards() {
        const container = new St.BoxLayout({vertical: true, style_class: 'ai-usage-overview-section'});

        const cards = this._popupOverviewCards || [];
        if (cards.length === 0) {
            container.add_child(this.buildEmptyState());
            return container;
        }

        for (const card of cards) {
            const button = this._buildOverviewCard(card);
            button.connect('clicked', () => {
                this._selectProvider(card.providerId || '');
                this._updateContent();
            });
            container.add_child(button);
        }

        return container;
    },

    buildEmptyState() {
        let msg = 'No AI tools detected';
        if (this._isLoading)
            msg = 'Loading...';
        else if (this._lastError)
            msg = this._lastError;

        const box = new St.BoxLayout({vertical: true, style_class: 'ai-usage-empty-state-section'});
        const label = new St.Label({text: msg, style_class: 'ai-usage-empty-state-label'});
        label.clutter_text.line_wrap = true;
        label.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
        label.clutter_text.ellipsize = Pango.EllipsizeMode.NONE;
        box.add_child(label);
        return box;
    },
};
