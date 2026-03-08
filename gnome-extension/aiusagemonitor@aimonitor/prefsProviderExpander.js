import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import Gtk from 'gi://Gtk';

import {createDropdownRow, createFieldRow} from './prefsCommonRows.js';
import {
    descriptorCapabilities,
    providerActiveSourceLabel,
    providerAvailabilityText,
    providerCapabilitiesText,
    providerFallbackLabel,
    providerPreferredSourceLabel,
    providerSourceModeLabel,
    providerSourceReason,
    providerStatusSummaryLabel,
    providerStatusTags,
    providerStrategyText,
    providerSubtitle,
    sourceModeDisplayLabel,
    sourceModeOptions,
} from './prefsProviderPresentation.js';

export function providerIconWidget(extensionPath, descriptor) {
    const branding = descriptor?.branding || {};
    const assetName = branding.assetName || (branding.iconKey ? `${branding.iconKey}.svg` : '');
    if (!assetName)
        return null;
    try {
        const file = Gio.File.new_for_path(`${extensionPath}/images/${assetName}`);
        return new Gtk.Image({
            gicon: new Gio.FileIcon({file}),
            pixel_size: 16,
            valign: Gtk.Align.CENTER,
        });
    } catch (_error) {
        return null;
    }
}

export function normalizedProviderSettings(descriptor, providerMap) {
    const stored = providerMap.get(descriptor.id) || {};
    const sourceModes = sourceModeOptions(descriptor);
    const defaultSource = sourceModes.length > 0 ? sourceModes[0] : 'auto';
    return {
        ...stored,
        id: descriptor.id,
        enabled: stored.enabled !== false,
        source: stored.source || defaultSource,
    };
}

export function createProviderConfigExpander(extensionPath, descriptor, providerSettings, providerState, onSetField) {
    const expander = new Adw.ExpanderRow({
        title: descriptor.displayName || descriptor.shortName || descriptor.id,
        subtitle: providerSubtitle(descriptor, providerState),
    });
    expander.add_css_class('ai-usage-provider-expander');

    const providerIcon = providerIconWidget(extensionPath, descriptor);
    if (providerIcon)
        expander.add_prefix(providerIcon);

    const sourceBadge = new Gtk.Label({
        label: providerSourceModeLabel(descriptor, providerState),
        valign: Gtk.Align.CENTER,
    });
    sourceBadge.add_css_class('ai-usage-source-badge');
    expander.add_suffix(sourceBadge);

    const preferredBadge = new Gtk.Label({
        label: providerPreferredSourceLabel(providerSettings, providerState),
        valign: Gtk.Align.CENTER,
    });
    preferredBadge.add_css_class('ai-usage-source-badge-secondary');
    expander.add_suffix(preferredBadge);

    const activeBadge = new Gtk.Label({
        label: providerActiveSourceLabel(descriptor, providerState),
        valign: Gtk.Align.CENTER,
    });
    activeBadge.add_css_class('ai-usage-source-badge-secondary');
    expander.add_suffix(activeBadge);

    const statusBadge = new Gtk.Label({
        label: providerStatusSummaryLabel(descriptor, providerState),
        valign: Gtk.Align.CENTER,
    });
    statusBadge.add_css_class('ai-usage-source-badge-secondary');
    expander.add_suffix(statusBadge);

    const configureButton = new Gtk.Button({label: 'Configure', valign: Gtk.Align.CENTER});
    configureButton.add_css_class('flat');
    configureButton.connect('clicked', () => {
        expander.set_expanded(!expander.get_expanded());
    });
    expander.add_suffix(configureButton);

    const enabledSwitch = new Gtk.Switch({active: providerSettings.enabled !== false, valign: Gtk.Align.CENTER});
    const enabledLabel = new Gtk.Label({
        label: providerSettings.enabled !== false ? 'Enabled' : 'Disabled',
        valign: Gtk.Align.CENTER,
    });
    enabledLabel.add_css_class('dim-label');
    enabledSwitch.connect('notify::active', widget => {
        enabledLabel.set_label(widget.get_active() ? 'Enabled' : 'Disabled');
        onSetField(descriptor.id, 'enabled', widget.get_active() ? 'true' : 'false');
    });
    expander.add_suffix(enabledLabel);
    expander.add_suffix(enabledSwitch);

    const statusSummary = providerStatusSummaryLabel(descriptor, providerState);
    const fallbackSummary = providerFallbackLabel(providerState);
    const statusRow = new Adw.ActionRow({
        title: 'Status',
        subtitle: [statusSummary, fallbackSummary].filter(Boolean).join(' · ') ||
            providerStatusTags(descriptor, providerState).join(' · ') ||
            'Unknown',
    });
    statusRow.add_css_class('ai-usage-provider-field');
    expander.add_row(statusRow);

    const reasonRow = new Adw.ActionRow({
        title: 'Why this source',
        subtitle: providerSourceReason(providerSettings, providerState),
    });
    reasonRow.add_css_class('ai-usage-provider-field');
    expander.add_row(reasonRow);

    const capabilitiesRow = new Adw.ActionRow({
        title: 'Capabilities',
        subtitle: providerCapabilitiesText(descriptor, providerState),
    });
    capabilitiesRow.add_css_class('ai-usage-provider-field');
    expander.add_row(capabilitiesRow);

    const strategyRow = new Adw.ActionRow({
        title: 'Source strategy',
        subtitle: providerStrategyText(providerSettings, providerState),
    });
    strategyRow.add_css_class('ai-usage-provider-field');
    expander.add_row(strategyRow);

    const availabilityRow = new Adw.ActionRow({
        title: 'Availability',
        subtitle: providerAvailabilityText(descriptor, providerState),
    });
    availabilityRow.add_css_class('ai-usage-provider-field');
    expander.add_row(availabilityRow);

    const sourceOptions = sourceModeOptions(descriptor);
    if (sourceOptions.length > 1) {
        const labels = sourceOptions.map(mode => sourceModeDisplayLabel(mode));
        const currentSourceIndex = sourceOptions.indexOf(providerSettings.source || sourceOptions[0]);
        const sourceRow = createDropdownRow(
            'Source',
            labels,
            currentSourceIndex >= 0 ? currentSourceIndex : 0,
            selected => onSetField(descriptor.id, 'source', sourceOptions[selected])
        );
        sourceRow.add_css_class('ai-usage-provider-field');
        expander.add_row(sourceRow);
    } else if (sourceOptions.length === 1) {
        const sourceRow = new Adw.ActionRow({
            title: 'Source',
            subtitle: sourceModeDisplayLabel(sourceOptions[0]),
        });
        sourceRow.add_css_class('ai-usage-provider-field');
        expander.add_row(sourceRow);
    }

    let hasField = false;
    for (const field of descriptor.configFields || []) {
        hasField = true;
        const fieldRow = createFieldRow(
            field,
            providerSettings[field.key] || '',
            value => onSetField(descriptor.id, field.key, value || '__null__')
        );
        fieldRow.add_css_class('ai-usage-provider-field');
        expander.add_row(fieldRow);
    }

    if (!hasField && sourceOptions.length <= 1) {
        const noOptionsRow = new Adw.ActionRow({
            title: 'No additional options',
            subtitle: 'This provider only supports enable/disable.',
        });
        noOptionsRow.add_css_class('ai-usage-provider-field');
        expander.add_row(noOptionsRow);
    }

    return expander;
}

export {descriptorCapabilities};
