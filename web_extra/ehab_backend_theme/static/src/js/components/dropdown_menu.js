odoo.define("ehab_backend_theme.DropdownMenu", function(require) {
    'use strict';

    const DropdownMenu = require('web.DropdownMenu');
    const { patch } = require('web.utils');
    const { device } = require("web.config");
    const { hooks } = owl;
    const { useExternalListener, useState } = hooks;

    patch(DropdownMenu.prototype, 'ehab_backend_theme.DropdownMenu', {
        willStart() {
            this._super(...arguments);
            this.state.open = this.props.startOpen;
        },
        /**
         * @override
         * @param {OwlEvent} ev
         */
        _onItemSelected(ev) {
            if (!this.props.manualyClose) {
                this._super(...arguments);
            } else {
                return
            }
        },
        get dropdownMenuAlignClass() {
            if (this.env.device.isMobile && !this.state.open) {
                this._super(...arguments);
            } else {
                return '';
            }
        },
        /**
         * @override
         * @param {OwlEvent} ev
         */
        _onWindowClick(ev) {
            if (!this.props.manualyClose) {
                this._super(...arguments);
            } else {
                if (
                    this.state.open &&
                    !this.el.contains(ev.target) &&
                    !this.el.contains(document.activeElement)
                ) {
                    if (document.body.classList.contains("modal-open")) {
                        // retrieve the active modal and check if the dropdown is a child of this modal
                        const modal = this.el.closest(".modal[role='dialog']:not(.o_inactive_modal)")
                        if (!modal) {
                            return;
                        }
                    }
                    // check for an active open bootstrap calendar like the filter dropdown inside the search panel)
                    if (document.querySelector('body > .bootstrap-datetimepicker-widget')) {
                        return;
                    }
                    if (!this.props.manualyClose) {
                        this.state.open = false;
                    }
                    if (this.props.startOpen && this.el.contains(ev.target)) {
                        this.state.open = true;
                        this.props.startOpen = false;
                    } else {
                        if ($(ev.target).parents('.o_action_ejad').length) {
                            this.state.open = false;
                        }
                    }
                } else {
                    if (!this.state.open && !this.props.startOpen && $(document.querySelectorAll('.o_action_ejad')).length === 1) {
                        this.state.open = true;
                    }
                }
            }
        },
    });
    DropdownMenu.props['startOpen'] = { type: Boolean, optional: 1 }
    DropdownMenu.props['manualyClose'] = { type: Boolean, optional: 1 }
});