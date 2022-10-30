odoo.define("ehab_backend_theme.ActionMenus", function(require) {
    'use strict';

    const ActionMenus = require('web.ActionMenus');
    const { patch } = require('web.utils');
    const { device } = require("web.config");
    patch(ActionMenus.prototype, 'ehab_backend_theme.ActionMenus', {

        mounted() {
            this._super(...arguments);

            if (this.actionItems.length === 0 && this.printItems.length === 0) {
                var $sidebarDrw = document.querySelector('.o_sidebar_drw');
                $sidebarDrw.classList.add('d-none');
            };
            this.el && this.el.childNodes.forEach(childNode => {
                childNode.classList && childNode.classList.remove('ad_active');
            });
            this.el && this.el.childNodes && this.el.childNodes[0].classList.add('ad_active');
            var $oSidebarDrw = this.el.querySelector('.o_sidebar_drw');
            var $actions = document.querySelector('.o_action');
            if (device.isMobile && (this.el.classList && this.el.classList.contains('o_drw_in') ||
                    ($actions && $actions.classList.contains('o_open_sidebar')))) {
                this.el && this.el.classList.remove('o_drw_in');
                $actions && $actions.classList.remove('o_open_sidebar');
                $oSidebarDrw && $oSidebarDrw.classList.remove('fa-chevron-right');
                $oSidebarDrw && $oSidebarDrw.classList.add('fa-chevron-left')
            };
            if ((this.actionItems.length > 0 || this.printItems.length > 0) &&
                this.el && this.el.classList && this.el.classList.contains('o_drw_in')) {
                $actions.classList.add('o_open_sidebar');
            } else if ((this.actionItems.length > 0 || this.printItems.length > 0) &&
                this.el && this.el.classList && !this.el.classList.contains('o_drw_in') &&
                $actions && $actions.classList.contains('o_open_sidebar')) {
                this.el.classList.add('o_drw_in');
                $oSidebarDrw && $oSidebarDrw.classList.add('fa-chevron-right');
                $oSidebarDrw && $oSidebarDrw.classList.remove('fa-chevron-left')
            };
        },

        onActionMore(ev) {
            var $cp_action_menus = ev.target && ev.target.parentNode;
            var $actions = document.querySelector('.o_action');

            $cp_action_menus.classList.toggle('o_drw_in');
            ev.target.classList.toggle('fa-chevron-left');
            ev.target.classList.toggle('fa-chevron-right');
            $actions.classList.toggle('o_open_sidebar');
        }
    });
});