import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';

export const OVERVIEW_MAX_PROVIDERS = 3;

export function createOverviewSelectionRow(descriptors, config, onSave) {
    const row = new Adw.PreferencesRow();
    row.add_css_class('ai-usage-overview-selection-row');

    const wrapper = new Gtk.Box({
        orientation: Gtk.Orientation.VERTICAL,
        spacing: 6,
        margin_top: 4,
        margin_bottom: 2,
        margin_start: 4,
        margin_end: 4,
        hexpand: true,
    });
    wrapper.add_css_class('ai-usage-overview-selection-box');

    const header = new Gtk.Box({orientation: Gtk.Orientation.HORIZONTAL, spacing: 8, hexpand: true});
    const title = new Gtk.Label({label: 'Overview tab providers', xalign: 0, hexpand: true});
    title.add_css_class('heading');
    const selectedCountLabel = new Gtk.Label({label: '', xalign: 1});
    selectedCountLabel.add_css_class('dim-label');

    header.append(title);
    header.append(selectedCountLabel);
    wrapper.append(header);

    const hint = new Gtk.Label({
        label: 'Pick up to 3 providers for overview cards. This selection is separate from normal enabled provider tabs.',
        xalign: 0,
        wrap: true,
    });
    hint.add_css_class('caption');
    hint.add_css_class('dim-label');
    wrapper.append(hint);

    const grid = new Gtk.Grid({
        column_spacing: 14,
        row_spacing: 6,
        column_homogeneous: true,
        hexpand: true,
    });
    grid.add_css_class('ai-usage-overview-grid');

    const currentOverview = Array.isArray(config.overviewProviderIds)
        ? config.overviewProviderIds.slice(0, OVERVIEW_MAX_PROVIDERS)
        : [];
    const switches = [];

    const refreshSwitchStates = () => {
        const selectedCount = switches.filter(item => item.widget.get_active()).length;
        selectedCountLabel.set_label(`Selected ${selectedCount}/${OVERVIEW_MAX_PROVIDERS}`);
        for (const item of switches)
            item.widget.set_sensitive(item.widget.get_active() || selectedCount < OVERVIEW_MAX_PROVIDERS);
    };

    const columnCount = descriptors.length > 9 ? 3 : 2;
    descriptors.forEach((descriptor, index) => {
        const providerId = descriptor.id;
        const checkButton = new Gtk.CheckButton({
            label: descriptor.shortName || descriptor.displayName || providerId,
            active: currentOverview.includes(providerId),
            halign: Gtk.Align.START,
            valign: Gtk.Align.CENTER,
            hexpand: true,
        });
        checkButton.add_css_class('ai-usage-overview-check');
        checkButton.set_tooltip_text(descriptor.displayName || providerId);
        checkButton.connect('toggled', widget => {
            let nextIds = Array.isArray(config.overviewProviderIds) ? [...config.overviewProviderIds] : [];
            nextIds = nextIds.filter(id => id !== providerId);
            if (widget.get_active()) {
                if (nextIds.length >= OVERVIEW_MAX_PROVIDERS) {
                    widget.set_active(false);
                    return;
                }
                nextIds.push(providerId);
            }
            config.overviewProviderIds = nextIds.slice(0, OVERVIEW_MAX_PROVIDERS);
            onSave(config);
            refreshSwitchStates();
        });

        const col = index % columnCount;
        const rowIndex = Math.floor(index / columnCount);
        grid.attach(checkButton, col, rowIndex, 1, 1);
        switches.push({providerId, widget: checkButton});
    });

    wrapper.append(grid);
    row.set_child(wrapper);
    refreshSwitchStates();
    return row;
}
