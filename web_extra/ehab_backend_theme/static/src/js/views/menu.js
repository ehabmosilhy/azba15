/** @odoo-module **/

import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { useEffect, useService } from "@web/core/utils/hooks";

import { patch } from 'web.utils';
import Widget from 'web.Widget';
import { qweb } from 'web.core';

patch(DropdownItem.prototype, '@ehab_backend_theme/static/src/js/views/menu.js', {
    willStart() {
        this._super(...arguments);
        useEffect(
            () => {
                if (this.props.payload && this.props.payload.id) {
                    if (this.props.payload.id === "logout") {
                        this.props.payload.callback = this._onClickLogout.bind(this);
                    }
                }
            },
            () => []
        );
    },
    _onClickLogout: function(e) {
        let template = $(qweb.render('LogoutMessage', {}));
        var modal = template.appendTo(this.el.closest('body'));
        document.querySelector('.oe_cu_logout_yes').addEventListener('click', this._onClickLogoutBtn, this.el)
        document.querySelector('.mb-control-close').addEventListener('click', this._onClickRemoveBtn, this.el)
        return modal
    },
    _onClickRemoveBtn: function(ev) {
        $('.message-box').remove();
    },
    _onClickLogoutBtn: function(ev) {
        window.location.href = "/web/session/logout?redirect=/web/login";
    },
});