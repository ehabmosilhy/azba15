odoo.define("ehab_backend_theme.SearchBar", function(require) {
    'use strict';

    const SearchBar = require('web.SearchBar');
    var config = require('web.config');
    var core = require('web.core');
    const { patch } = require('web.utils');

    patch(SearchBar.prototype, 'ehab_backend_theme.SearchBar', {

        mounted() {
            this._super(...arguments);
            this.isMobileView = config.device.isMobile;
            this.searchFacets = this.model.get('facets');
            this.el.classList.toggle('d-none', this.isMobileView);
            this._manageFacets();
        },

        patched() {
            this.searchFacets = this.model.get('facets');
            this._manageFacets();
        },

        _manageFacets: function(detachToInput) {
            detachToInput = _.isUndefined(detachToInput) ? false : detachToInput;

            var searchArea = 0;
            var deviceWidth = window.innerWidth;
            var mobileClass = this.isMobileView ? '_mobile' : '';
            if (document.body.classList.contains("modal-open")) {
                deviceWidth = $(document.querySelector('.modal-dialog')) ? $(document.querySelector('.modal-dialog'))[0].clientWidth : window.innerWidth;
            }
            var $o_searchview = this.el.closest('.o_searchview' + mobileClass);
            var $o_searchview_input = this.el.querySelector('.o_searchview_input')
            var $parentNode = this.el.parentNode;
            var $o_search_recs = $parentNode.querySelector('.o_search_recs' + mobileClass)
            var $o_search_rec_ul = $parentNode.querySelector('.o_search_rec_ul' + mobileClass);
            for (var i = 0; i < this.searchFacets.length; i++) {
                const $searchFacet = this.el.querySelectorAll('[facet-count="' + i + '"]');
                $searchFacet.forEach(facet => {
                    searchArea += facet.clientWidth;
                    if (!detachToInput && searchArea !== 0) {
                        if ($o_search_rec_ul && !this.isMobileView && searchArea > ((deviceWidth / 2) - 250)) {
                            $o_search_rec_ul.appendChild(facet);
                        };
                    } else {
                        if ($o_searchview_input && $o_searchview_input.parentNode) {
                            $o_searchview_input.parentNode.insertBefore(facet, $o_searchview_input);
                        };
                    };
                });
            };

            setTimeout(function() {
                if ($o_search_rec_ul) {
                    var hasDropDownFacet = Boolean($o_search_rec_ul.childNodes.length);
                    $o_searchview.classList.toggle('show', hasDropDownFacet);
                    $o_search_recs && $o_search_recs.classList.toggle('o_hidden', !hasDropDownFacet);
                    $o_search_rec_ul.classList.toggle('show', hasDropDownFacet);
                    $o_search_rec_ul.classList.toggle('o_hidden', !hasDropDownFacet);
                }
            }, 10);
        },
    });
});