import Adw from 'gi://Adw';
import Gdk from 'gi://Gdk';
import Gtk from 'gi://Gtk';
import {ExtensionPreferences} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

import {runBackendAsync} from './prefsBackend.js';
import {createGeneralGroup} from './prefsGeneralSection.js';
import {createOverviewSelectionRow} from './prefsOverviewSelection.js';
import {
    createProviderConfigExpander,
    normalizedProviderSettings,
} from './prefsProviderExpander.js';

function clearGroup(group) {
    while (group.get_first_child())
        group.remove(group.get_first_child());
}

export default class AIUsageMonitorPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        this._ensurePrefsCssLoaded();

        const settings = this.getSettings();
        const page = new Adw.PreferencesPage({
            title: 'Settings',
            icon_name: 'preferences-system-symbolic',
        });

        const generalGroup = createGeneralGroup(settings);

        const overviewGroup = new Adw.PreferencesGroup({
            title: 'Overview',
            description: 'Choose providers for overview cards. This selection is separate from normal enabled provider tabs.',
        });

        const providerGroup = new Adw.PreferencesGroup({
            title: 'Providers',
            description: 'Configure providers with enabled state, preferred source, active source and source status.',
        });

        const actionsGroup = new Adw.PreferencesGroup({
            title: 'Footer actions',
            description: 'Maintenance actions for settings and provider descriptors.',
        });

        const reloadRow = new Adw.ActionRow({
            title: 'Reload shared settings',
            subtitle: 'Fetch latest provider descriptors and status.',
        });
        reloadRow.add_css_class('ai-usage-actions-row');
        const reloadButton = new Gtk.Button({label: 'Reload', valign: Gtk.Align.CENTER});
        reloadButton.add_css_class('suggested-action');
        reloadRow.add_suffix(reloadButton);
        reloadRow.activatable_widget = reloadButton;
        actionsGroup.add(reloadRow);

        page.add(generalGroup);
        page.add(overviewGroup);
        page.add(providerGroup);
        page.add(actionsGroup);
        window.add(page);

        const renderSharedSections = () => {
            clearGroup(overviewGroup);
            clearGroup(providerGroup);

            overviewGroup.add(new Adw.ActionRow({title: 'Loading overview providers…'}));
            providerGroup.add(new Adw.ActionRow({
                title: 'Loading provider config…',
                subtitle: 'Fetching shared backend state',
            }));

            this._loadConfigPayloadAsync((error, configPayload) => {
                clearGroup(overviewGroup);
                clearGroup(providerGroup);

                const descriptors = configPayload?.descriptors || [];
                const sortedDescriptors = [...descriptors].sort((a, b) =>
                    String(a.shortName || a.displayName || a.id).localeCompare(
                        String(b.shortName || b.displayName || b.id)
                    )
                );
                const config = configPayload?.config || {providers: [], overviewProviderIds: []};
                const stateProviders = (configPayload?.state && configPayload.state.providers) || [];
                const providerMap = new Map((config.providers || []).map(provider => [provider.id, provider]));
                const stateMap = new Map(stateProviders.map(provider => [provider.id, provider]));

                if (error) {
                    const message = error.message || String(error);
                    overviewGroup.add(new Adw.ActionRow({
                        title: 'Failed to load shared provider config',
                        subtitle: message,
                    }));
                    providerGroup.add(new Adw.ActionRow({
                        title: 'Failed to load shared provider config',
                        subtitle: message,
                    }));
                    return;
                }

                overviewGroup.add(createOverviewSelectionRow(
                    sortedDescriptors,
                    config,
                    nextConfig => this._saveSharedConfig(nextConfig)
                ));

                for (const descriptor of sortedDescriptors) {
                    const providerSettings = normalizedProviderSettings(descriptor, providerMap);
                    const providerState = stateMap.get(descriptor.id) || {};
                    providerGroup.add(createProviderConfigExpander(
                        this.path,
                        descriptor,
                        providerSettings,
                        providerState,
                        (providerId, field, value) => this._setProviderField(providerId, field, value)
                    ));
                }
            });
        };

        reloadButton.connect('clicked', () => renderSharedSections());
        renderSharedSections();
    }

    _ensurePrefsCssLoaded() {
        if (this._prefsCssLoaded)
            return;
        try {
            const provider = new Gtk.CssProvider();
            provider.load_from_path(`${this.path}/prefs.css`);
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            );
            this._prefsCssLoaded = true;
        } catch (_error) {
            this._prefsCssLoaded = true;
        }
    }

    _loadConfigPayloadAsync(callback) {
        runBackendAsync(this.path, ['config-ui-full'], (error, payload) => {
            if (error)
                callback(error, {config: {providers: []}, descriptors: []});
            else
                callback(null, payload);
        });
    }

    _setProviderField(providerId, field, value) {
        runBackendAsync(this.path, ['config-set-provider', providerId, field, value], () => {});
    }

    _saveSharedConfig(config) {
        runBackendAsync(this.path, ['config-save-json', JSON.stringify(config)], () => {});
    }
}
