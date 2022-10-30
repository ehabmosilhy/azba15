/** @odoo-module **/

import { SearchBar } from "@web/search/search_bar/search_bar";
import { patch } from 'web.utils';

patch(SearchBar.prototype, 'web/static/src/search/search_bar/search_bar.js', {
    mounted() {
        this.manageFacets();
    },

    patched() {
        this.manageFacets();
    },

    manageFacets(detachToInput) {
        if (this.state.query.length) {
            return;
        }
        var searchArea = 0;
        var deviceWidth = window.innerWidth;
        var mobileClass = this.isMobileView ? '_mobile' : '';
        if (document.body.classList.contains("modal-open")) {
            deviceWidth = $(document.querySelector('.modal-dialog')) ? $(document.querySelector('.modal-dialog'))[0].clientWidth : window.innerWidth;
        }
        var $o_searchview = this.el.querySelector('.o_searchview' + mobileClass);
        var $o_searchview_input = this.el.querySelector('.o_searchview_input')
        var $parentNode = this.el.parentNode;
        var $o_search_recs = $parentNode.querySelector('.o_search_recs' + mobileClass)
        var $o_search_rec_ul = $parentNode.querySelector('.o_search_rec_ul' + mobileClass);
        const $searchItem = this.el.querySelectorAll('.o_searchview_facet');
        for (var i = 0; i < $searchItem.length; i++) {
            const $searchFacet = this.el.querySelectorAll('[facet-count="' + i + '"]');
            $searchFacet.forEach(function(facet, index) {
                searchArea += facet.clientWidth;
                if (!detachToInput && searchArea !== 0) {
                    if ($o_search_rec_ul && !self.isMobileView && searchArea > ((deviceWidth / 2) - 250)) {
                        $o_search_rec_ul.appendChild(facet);
                    };
                } else {
                    if ($o_searchview_input && $o_searchview_input.parentNode) {
                        $o_searchview_input.parentNode.insertBefore(facet, $o_searchview_input);
                    };
                };
            });
        }

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
    _onClickSearchButton(e) {
        var parentNode = this.el.closest('.o_view_controller');
        var searchOptions = e.target.closest('.o_control_panel').querySelector('.o_search_options');
        parentNode.classList.toggle('ad_open_search');
        searchOptions.classList.toggle('o_hidden');
    },
});