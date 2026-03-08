export const IndicatorContentFlowMixin = {
    _updateContent() {
        if (this._destroyed || !this._contentBox)
            return;
        this._updateSwitcher();
        this._resetBoxChildren(this._contentBox);
        this._selectedPopupProvider = this._resolveSelectedProviderId(this._selectedPopupProvider);
        this._contentBox.add_child(this._buildSelectedContent());
        this.menu.box.queue_relayout();
    },

    _buildSelectedContent() {
        if (this._selectedPopupProvider === 'overview')
            return this.buildOverviewCards();

        if (!this._selectedPopupProvider)
            return this.buildEmptyState();

        const selectedProvider = this._providerById(this._selectedPopupProvider);
        if (!selectedProvider)
            return this.buildEmptyState();

        return this.buildProviderDetailSection(selectedProvider);
    },

    _updateSwitcher() {
        if (this._destroyed || !this._switcherBox)
            return;
        this._resetBoxChildren(this._switcherBox);
        this._switcherBox.add_child(this.buildProviderTabsRow());
    },

    _resetBoxChildren(box) {
        if (!box)
            return;
        box.destroy_all_children();
    },
};
