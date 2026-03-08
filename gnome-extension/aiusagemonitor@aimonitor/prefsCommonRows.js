import Adw from 'gi://Adw';
import Gtk from 'gi://Gtk';

export function createDropdownRow(title, labels, selectedIndex, onChange) {
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

export function createEntryRow(title, value, placeholder, secret, onCommit) {
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

export function createFieldRow(field, value, onCommit) {
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
