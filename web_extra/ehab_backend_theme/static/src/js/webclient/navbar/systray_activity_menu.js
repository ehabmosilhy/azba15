/** @odoo-module **/

import ActivityMenu from '@mail/js/systray/systray_activity_menu';
import { _t } from 'web.core';
import Widget from 'web.Widget';

ActivityMenu.include({
    //--------------------------------------------------
    // Private
    //--------------------------------------------------
    /**
     * @override
     */
    _onActivityFilterClick: function(event) {
        var self = this;
        $('.o_menu_systray').removeClass('show');
        this._super.apply(this, arguments);
    },
    /**
     * @override
     */
    _onActivityMenuShow: function() {
        var element = document.querySelector('.dropdown.show');
        if (element) {
            var button = element.querySelector('button');
            if (button) {
                button.click();
            }
        }
        this._super.apply(this, arguments);
    },
});