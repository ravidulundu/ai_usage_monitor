import Clutter from 'gi://Clutter';
import Pango from 'gi://Pango';
import St from 'gi://St';

export const IndicatorHeaderMixin = {
    _buildHeaderTitleRow(provider) {
        const titleRow = new St.BoxLayout({vertical: false, style_class: 'ai-usage-header-title-row'});

        titleRow.add_child(new St.Label({
            text: provider.displayName || '',
            style_class: 'ai-usage-provider-title-large',
        }));

        titleRow.add_child(new St.Widget({x_expand: true}));

        if (provider.planLabel) {
            titleRow.add_child(new St.Label({
                text: provider.planLabel,
                style_class: 'ai-usage-provider-plan-label',
                x_align: Clutter.ActorAlign.END,
            }));
        }
        return titleRow;
    },

    _buildHeaderSourceRow(sourceModeLabel, activeSourceLabel, sourceStatusTags) {
        if (!sourceModeLabel && !activeSourceLabel && sourceStatusTags.length === 0)
            return null;
        const sourceRow = new St.BoxLayout({
            vertical: false,
            style_class: 'ai-usage-source-row ai-usage-provider-header-source-row',
        });

        if (sourceModeLabel) {
            sourceRow.add_child(new St.Label({
                text: sourceModeLabel,
                style_class: 'ai-usage-source-pill ai-usage-source-pill-mode',
            }));
        }
        if (activeSourceLabel) {
            sourceRow.add_child(new St.Label({
                text: activeSourceLabel,
                style_class: 'ai-usage-source-pill ai-usage-source-pill-active',
            }));
        }
        for (const tag of sourceStatusTags) {
            if (!tag)
                continue;
            sourceRow.add_child(new St.Label({
                text: String(tag),
                style_class: 'ai-usage-source-pill ai-usage-source-pill-status',
            }));
        }
        return sourceRow;
    },

    _buildHeaderSourceDetails(provider, sourceReasonText) {
        if (!sourceReasonText && !provider.sourceDetails)
            return null;
        const details = new St.Label({
            text: sourceReasonText || provider.sourceDetails,
            style_class: 'ai-usage-provider-source-details',
        });
        details.clutter_text.line_wrap = false;
        details.clutter_text.ellipsize = Pango.EllipsizeMode.END;
        return details;
    },

    _buildHeaderStatusRow(statusVisible, statusBadgeLabel, statusDetails, statusTone) {
        if (!(statusVisible && statusBadgeLabel))
            return null;
        const statusRow = new St.BoxLayout({
            vertical: false,
            style_class: 'ai-usage-provider-status-row ai-usage-provider-header-status-row',
        });
        statusRow.add_child(new St.Label({
            text: statusBadgeLabel,
            style_class: 'ai-usage-provider-status-pill',
        }));
        this._applyToneClass(statusRow.get_last_child(), statusTone === 'error' ? 'error' : 'warn');

        if (statusDetails) {
            const details = new St.Label({
                text: statusDetails,
                style_class: 'ai-usage-provider-status-details',
            });
            details.clutter_text.ellipsize = Pango.EllipsizeMode.END;
            details.x_expand = true;
            statusRow.add_child(details);
        }
        return statusRow;
    },

    _buildHeaderErrorLabel(provider) {
        if (!(provider.errorState?.hasError && provider.errorState.message))
            return null;
        const errorLabel = new St.Label({
            text: provider.errorState.message,
            style_class: 'ai-usage-error',
        });
        errorLabel.clutter_text.line_wrap = true;
        errorLabel.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
        errorLabel.clutter_text.ellipsize = Pango.EllipsizeMode.NONE;
        return errorLabel;
    },

    buildHeaderSection(provider) {
        const section = new St.BoxLayout({vertical: true, style_class: 'ai-usage-header-section ai-usage-provider-header'});
        const sourcePresentation = provider?.sourcePresentation || {};
        const statusPresentation = provider?.statusPresentation || {};
        section.add_child(this._buildHeaderTitleRow(provider));

        section.add_child(new St.Label({
            text: provider.updatedText || '',
            style_class: 'ai-usage-provider-updated',
        }));

        const sourceRow = this._buildHeaderSourceRow(
            sourcePresentation?.modeLabel || '',
            sourcePresentation?.activeSourceLabel || '',
            Array.isArray(sourcePresentation?.statusTags) ? sourcePresentation.statusTags : []
        );
        if (sourceRow)
            section.add_child(sourceRow);

        if (provider.subtitle) {
            section.add_child(new St.Label({
                text: provider.subtitle,
                style_class: 'ai-usage-provider-subtitle',
            }));
        }

        const sourceDetails = this._buildHeaderSourceDetails(provider, sourcePresentation?.reasonText || '');
        if (sourceDetails)
            section.add_child(sourceDetails);
        const statusRow = this._buildHeaderStatusRow(
            statusPresentation?.visible === true,
            statusPresentation?.badgeLabel || '',
            statusPresentation?.details || '',
            statusPresentation?.tone || 'warn'
        );
        if (statusRow)
            section.add_child(statusRow);
        const errorLabel = this._buildHeaderErrorLabel(provider);
        if (errorLabel)
            section.add_child(errorLabel);

        return section;
    },

    buildSwitchingStateSection(provider, forceFallback = false) {
        const switchingState = provider?.switchingState;
        const title = typeof switchingState?.title === 'string' && switchingState.title
            ? switchingState.title
            : (forceFallback ? 'Switching account/source' : '');
        const message = typeof switchingState?.message === 'string' && switchingState.message
            ? switchingState.message
            : (forceFallback ? 'Refreshing usage for active identity' : '');
        if (!title && !message)
            return null;

        const section = new St.BoxLayout({vertical: true, style_class: 'ai-usage-switching-section'});

        if (title)
            section.add_child(new St.Label({text: title, style_class: 'ai-usage-switching-title'}));

        if (message) {
            const label = new St.Label({text: message, style_class: 'ai-usage-switching-message'});
            label.clutter_text.line_wrap = true;
            label.clutter_text.line_wrap_mode = Pango.WrapMode.WORD_CHAR;
            label.clutter_text.ellipsize = Pango.EllipsizeMode.NONE;
            section.add_child(label);
        }

        return section;
    },
};
