odoo.define("ehab_backend_theme.ControlPanel", function(require) {

    const ControlPanel = require('web.ControlPanel');
    const { device } = require("web.config");
    const { hooks } = owl;
    const { useExternalListener } = hooks;
    const { patch } = require('web.utils');

    patch(ControlPanel.prototype, 'ehab_backend_theme.ControlPanel', {

        setup() {
            this._super();
            this.isMobileView = device.isMobile;
            useExternalListener(window, 'click', this._onWindowClick);
        },

        _onClickSearchButton(e) {
            var parentNode = this.el.parentNode;
            var searchOptions = e.target.closest('.o_control_panel').querySelector('.o_search_options');
            parentNode.classList.toggle('ad_open_search');
            searchOptions.classList.toggle('o_hidden');
            searchOptions && searchOptions.childNodes.forEach(childNode => {
                childNode.classList && childNode.classList.remove('ad_active');
            });
            if (searchOptions.childNodes.length > 0) {
                searchOptions.childNodes[0].classList.add('ad_active');
            };
            if (device.isMobile) {
                var $modelBody = document.querySelector('.modal-body');
                if ($modelBody) { $modelBody.classList.add('ad_mobile_modal_body'); };

                var $adMobileSearchHeader = document.querySelector('.ad_mobile_search_header');
                if ($adMobileSearchHeader && $adMobileSearchHeader.firstChild &&
                    $adMobileSearchHeader.firstChild.classList.contains('o_searchview_input_container')) {
                    $adMobileSearchHeader.firstChild.classList.toggle('d-none');
                };
            };
        },

        _onShowMobileSearchFilter(e) {
            var $oSearchOptions = e.target.closest('.o_action') || e.target.closest('.o_widget_Discuss');
            var $modelBody = document.querySelector('.modal-body');
            $oSearchOptions && $oSearchOptions.classList.remove('ad_open_search');
            if ($modelBody) { $modelBody.classList.remove('ad_mobile_modal_body'); };
        },

        _onShowMobileSearchClear(e) {
            this.model.dispatch('clearQuery');
        },

        _onClickCpButtons(e) {
            var $oCpBottom = e.target.closest('.o_cp_bottom');
            $oCpBottom.classList.add('cp_open');
        },

        _onWindowClick(ev) {
            if (this.isMobileView &&
                !this.el.contains(document.activeElement) &&
                !this.el.contains(ev.target)) {
                var $oCpBottom = this.el.querySelector('.o_cp_bottom');
                $oCpBottom && $oCpBottom.classList.remove('cp_open');
            };
        }
    });

});