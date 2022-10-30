/** @odoo-module **/

import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import { device } from 'web.config';
const { Component, hooks } = owl;
const { useExternalListener } = hooks;


patch(ControlPanel.prototype, 'ehab_backend_theme/static/src/js/views/control_panel/control_panel.js', {

    setup() {
        this._super();
        this.isMobileView = device.isMobile;
        useExternalListener(window, 'click', this._onWindowClick);
    },
    _render() {
        return this._super();
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