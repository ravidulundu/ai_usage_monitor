import Adw from 'gi://Adw';

import {createDropdownRow} from './prefsCommonRows.js';

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
    {id: 'auto', shortName: 'Auto', displayName: 'Auto (active)'},
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

function _buildRefreshRow(settings) {
    const currentRefresh = settings.get_int('refresh-interval');
    const refreshIndex = REFRESH_VALUES.indexOf(currentRefresh);
    const row = createDropdownRow(
        'Refresh every',
        REFRESH_LABELS,
        refreshIndex,
        selected => settings.set_int('refresh-interval', REFRESH_VALUES[selected])
    );
    row.add_css_class('ai-usage-pref-compact-row');
    return row;
}

function _buildPanelToolRow(settings) {
    const currentTool = settings.get_string('panel-tool');
    const fallbackToolLabels = FALLBACK_PANEL_TOOLS.map(tool => tool.shortName);
    const fallbackToolValues = FALLBACK_PANEL_TOOLS.map(tool => tool.id);
    const fallbackToolIndex = fallbackToolValues.indexOf(currentTool);
    const row = createDropdownRow(
        'Panel tool',
        fallbackToolLabels,
        fallbackToolIndex >= 0 ? fallbackToolIndex : 0,
        selected => settings.set_string('panel-tool', fallbackToolValues[selected])
    );
    row.add_css_class('ai-usage-pref-compact-row');
    return row;
}

function _buildDisplayModeRow(settings) {
    const row = createDropdownRow(
        'Display style',
        DISPLAY_MODE_LABELS,
        settings.get_int('panel-display-mode'),
        selected => settings.set_int('panel-display-mode', selected)
    );
    row.add_css_class('ai-usage-pref-compact-row');
    return row;
}

export function createGeneralGroup(settings) {
    const group = new Adw.PreferencesGroup({
        title: 'General',
        description: 'Refresh cadence, panel tool and display style.',
    });
    group.add(_buildRefreshRow(settings));
    group.add(_buildPanelToolRow(settings));
    group.add(_buildDisplayModeRow(settings));
    return group;
}
