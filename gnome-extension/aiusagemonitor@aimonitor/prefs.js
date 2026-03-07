import Adw from 'gi://Adw';
import Gio from 'gi://Gio';
import Gtk from 'gi://Gtk';
import {ExtensionPreferences} from 'resource:///org/gnome/Shell/Extensions/js/extensions/prefs.js';

const REFRESH_LABELS = [
    '20 seconds',
    '1 minute',
    '2 minutes',
    '5 minutes',
    '10 minutes',
    '30 minutes',
];

const REFRESH_VALUES = [20, 60, 120, 300, 600, 1800];
const DISPLAY_MODE_LABELS = ['Ring and percentage', 'Ring only', 'Percentage only'];
const FALLBACK_PANEL_TOOLS = [
    {id: 'claude', shortName: 'Claude', displayName: 'Claude Code'},
    {id: 'codex', shortName: 'Codex', displayName: 'OpenAI Codex'},
    {id: 'gemini', shortName: 'Gemini', displayName: 'Gemini CLI'},
    {id: 'copilot', shortName: 'Copilot', displayName: 'GitHub Copilot'},
    {id: 'vertexai', shortName: 'Vertex', displayName: 'Vertex AI'},
    {id: 'openrouter', shortName: 'OpenRouter', displayName: 'OpenRouter'},
    {id: 'ollama', shortName: 'Ollama', displayName: 'Ollama'},
    {id: 'opencode', shortName: 'OpenCode', displayName: 'OpenCode'},
    {id: 'zai', shortName: 'z.ai', displayName: 'z.ai'},
    {id: 'kilo', shortName: 'Kilo', displayName: 'Kilo Code'},
    {id: 'minimax', shortName: 'MiniMax', displayName: 'MiniMax'},
];

function createDropdownRow(title, labels, selectedIndex, onChange) {
    const row = new Adw.ActionRow({title});

    const model = new Gtk.StringList();
    for (const label of labels)
        model.append(label);
    const dropdown = new Gtk.DropDown({model, valign: Gtk.Align.CENTER});
    dropdown.set_selected(selectedIndex >= 0 ? selectedIndex : 0);
    dropdown.connect('notify::selected', widget => {
        onChange(widget.get_selected());
    });

    row.add_suffix(dropdown);
    row.activatable_widget = dropdown;
    return row;
}

function runBackendAsync(extensionPath, args, callback) {
    let proc = new Gio.Subprocess({
        argv: ['python3', `${extensionPath}/scripts/fetch_all_usage.py`, ...args],
        flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
    });
    proc.init(null);
    proc.communicate_utf8_async(null, null, (self, result) => {
        try {
            let [, stdout, stderr] = self.communicate_utf8_finish(result);
            if (self.get_successful() && stdout?.trim()) {
                callback(null, JSON.parse(stdout.trim()));
                return;
            }
            callback(new Error(stderr?.trim() || 'Backend command failed'));
        } catch (error) {
            callback(error);
        }
    });
}

function createEntryRow(title, value, placeholder, secret, onCommit) {
    const row = new Adw.ActionRow({title});
    const entry = secret
        ? new Gtk.PasswordEntry({valign: Gtk.Align.CENTER, hexpand: true, placeholder_text: placeholder || ''})
        : new Gtk.Entry({valign: Gtk.Align.CENTER, hexpand: true, placeholder_text: placeholder || ''});

    entry.set_text(value || '');
    entry.connect('activate', widget => onCommit(widget.get_text()));
    entry.connect('notify::has-focus', widget => {
        if (!widget.has_focus)
            onCommit(widget.get_text());
    });

    row.add_suffix(entry);
    row.activatable_widget = entry;
    return row;
}

function createFieldRow(field, value, onCommit) {
    if (field.kind === 'choice') {
        const labels = (field.options || []).map(option => option.toUpperCase());
        const currentIndex = (field.options || []).indexOf(value || field.options?.[0]);
        return createDropdownRow(
            field.label,
            labels,
            currentIndex >= 0 ? currentIndex : 0,
            selected => onCommit(field.options[selected])
        );
    }

    return createEntryRow(
        field.label,
        value,
        field.placeholder || '',
        field.secret === true,
        onCommit
    );
}

export default class AIUsageMonitorPreferences extends ExtensionPreferences {
    fillPreferencesWindow(window) {
        const settings = this.getSettings();
        const page = new Adw.PreferencesPage({
            title: 'General',
            icon_name: 'preferences-system-symbolic',
        });

        const refreshGroup = new Adw.PreferencesGroup({
            title: 'Refresh Interval',
            description: 'How often to update usage data',
        });

        const currentRefresh = settings.get_int('refresh-interval');
        const refreshIndex = REFRESH_VALUES.indexOf(currentRefresh);
        refreshGroup.add(createDropdownRow(
            'Refresh every',
            REFRESH_LABELS,
            refreshIndex,
            selected => settings.set_int('refresh-interval', REFRESH_VALUES[selected])
        ));

        const panelGroup = new Adw.PreferencesGroup({
            title: 'Panel Display',
            description: 'Configure what appears in the top bar',
        });

        const currentTool = settings.get_string('panel-tool');
        const fallbackToolLabels = FALLBACK_PANEL_TOOLS.map(tool => tool.shortName);
        const fallbackToolValues = FALLBACK_PANEL_TOOLS.map(tool => tool.id);
        const fallbackToolIndex = fallbackToolValues.indexOf(currentTool);
        panelGroup.add(createDropdownRow(
            'Show in panel',
            fallbackToolLabels,
            fallbackToolIndex >= 0 ? fallbackToolIndex : 0,
            selected => settings.set_string('panel-tool', fallbackToolValues[selected])
        ));

        const modeIndex = settings.get_int('panel-display-mode');
        panelGroup.add(createDropdownRow(
            'Display style',
            DISPLAY_MODE_LABELS,
            modeIndex,
            selected => settings.set_int('panel-display-mode', selected)
        ));

        const providerGroup = new Adw.PreferencesGroup({
            title: 'Shared Provider Config',
            description: 'These settings are stored in ~/.config/ai-usage-monitor/config.json and shared by KDE and GNOME.',
        });

        const loadingRow = new Adw.ActionRow({
            title: 'Loading provider config…',
            subtitle: 'Fetching shared backend state',
        });
        providerGroup.add(loadingRow);

        page.add(refreshGroup);
        page.add(panelGroup);
        page.add(providerGroup);
        window.add(page);

        this._loadConfigPayloadAsync((error, configPayload) => {
            while (providerGroup.get_first_child())
                providerGroup.remove(providerGroup.get_first_child());

            const descriptors = configPayload?.descriptors || [];
            const config = configPayload?.config || {providers: []};
            const stateProviders = (configPayload?.state && configPayload.state.providers) || [];
            const providerMap = new Map((config.providers || []).map(provider => [provider.id, provider]));
            const stateMap = new Map(stateProviders.map(provider => [provider.id, provider]));

            if (error) {
                providerGroup.add(new Adw.ActionRow({
                    title: 'Failed to load shared provider config',
                    subtitle: error.message || String(error),
                }));
                return;
            }

            for (const descriptor of descriptors) {
            const providerSettings = providerMap.get(descriptor.id) || {};
            const providerState = stateMap.get(descriptor.id) || {};
            const baseName = descriptor.displayName || descriptor.id;
            let subtitle = baseName;
            if (providerState.installed === false)
                subtitle = `${baseName} · not detected`;
            else if (providerState.error)
                subtitle = `${baseName} · error`;
            else if (providerState.primaryMetric)
                subtitle = `${baseName} · ${Math.round(providerState.primaryMetric.usedPct || 0)}%`;
            const expander = new Adw.ExpanderRow({
                title: descriptor.shortName || descriptor.displayName,
                subtitle,
            });

            const enabledRow = new Adw.SwitchRow({
                title: 'Enabled',
                subtitle: 'Enable this provider in the shared backend',
                active: providerSettings.enabled !== false,
            });
            enabledRow.connect('notify::active', widget => {
                this._setProviderField(descriptor.id, 'enabled', widget.get_active() ? 'true' : 'false');
            });
            expander.add_row(enabledRow);

            if ((descriptor.sourceModes || []).length > 1) {
                const labels = descriptor.sourceModes.map(mode => mode.toUpperCase());
                const currentSource = providerSettings.source || descriptor.sourceModes[0];
                const currentSourceIndex = descriptor.sourceModes.indexOf(currentSource);
                expander.add_row(createDropdownRow(
                    'Source',
                    labels,
                    currentSourceIndex >= 0 ? currentSourceIndex : 0,
                    selected => this._setProviderField(descriptor.id, 'source', descriptor.sourceModes[selected])
                ));
            } else if ((descriptor.sourceModes || []).length === 1) {
                expander.add_row(new Adw.ActionRow({
                    title: 'Source',
                    subtitle: descriptor.sourceModes[0].toUpperCase(),
                }));
            }

            for (const field of descriptor.configFields || []) {
                expander.add_row(createFieldRow(
                    field,
                    providerSettings[field.key] || '',
                    value => this._setProviderField(descriptor.id, field.key, value || '__null__')
                ));
            }

            providerGroup.add(expander);
            }
        });
    }

    _loadConfigPayloadAsync(callback) {
        runBackendAsync(this.path, ['config-ui'], (error, payload) => {
            if (error)
                callback(error, {config: {providers: []}, descriptors: []});
            else
                callback(null, payload);
        });
    }

    _setProviderField(providerId, field, value) {
        runBackendAsync(this.path, ['config-set-provider', providerId, field, value], () => {});
    }
}
