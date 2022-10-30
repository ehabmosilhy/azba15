/** @odoo-module **/
import { Dropdown } from "@web/core/dropdown/dropdown";
const { patch } = require('web.utils');

import { useBus, useEffect, useService } from "@web/core/utils/hooks";
import { usePosition } from "@web/core/position/position_hook";
import { useDropdownNavigationCustom } from "./dropdown_navigation_hook";
import { ParentClosingMode } from "@web/core/dropdown/dropdown_item";
import { localization } from "@web/core/l10n/localization";

const { Component, core, hooks, useState, QWeb } = owl;
const { EventBus } = core;
const { onWillStart, useExternalListener, useRef, useSubEnv } = hooks;

const DIRECTION_CARET_CLASS = {
    bottom: "dropdown",
    top: "dropup",
    left: "dropleft",
    right: "dropright",
};
patch(Dropdown.prototype, '@ehab_backend_theme/js/components/dropdown.js', {
    /**
     * @override
     */
    setup() {
        /** @todo Add super */
        this.state = useState({
            open: this.props.startOpen,
            groupIsOpen: this.props.startOpen,
        });

        owl.hooks.onMounted(() => {
            if (document.body.classList.contains('modal-open')) {
                this.state.groupIsOpen = false;
                this.state.open = false;
            }
        });
        // Set up beforeOpen ---------------------------------------------------
        onWillStart(() => {
            if (this.state.open && this.props.beforeOpen) {
                return this.props.beforeOpen();
            }
        });

        // Set up dynamic open/close behaviours --------------------------------
        if (!this.props.manualOnly) {
            // Close on outside click listener
            useExternalListener(window, "click", this.onWindowClicked);
            // Listen to all dropdowns state changes
            useBus(Dropdown.bus, "state-changed", this.onDropdownStateChanged);
        }

        // Set up UI active element related behavior ---------------------------
        this.ui = useService("ui");
        useEffect(
            () => {
                Promise.resolve().then(() => {
                    this.myActiveEl = this.ui.activeElement;
                });
            },
            () => []
        );

        // Set up nested dropdowns ---------------------------------------------
        this.hasParentDropdown = this.env.inDropdown;
        useSubEnv({ inDropdown: true });

        // Set up key navigation -----------------------------------------------
        useDropdownNavigationCustom();
        // Set up toggler and positioning --------------------------------------
        /** @type {string} **/
        let position =
            this.props.position || (this.hasParentDropdown ? "right-start" : "bottom-start");
        let [direction, variant = "middle"] = position.split("-");
        if (localization.direction === "rtl") {
            if (["bottom", "top"].includes(direction)) {
                variant = variant === "start" ? "end" : "start";
            } else {
                direction = direction === "left" ? "right" : "left";
            }
            position = [direction, variant].join("-");
        }
        const positioningOptions = {
            popper: "menuRef",
            position,
        };
        this.directionCaretClass = DIRECTION_CARET_CLASS[direction];
        this.togglerRef = useRef("togglerRef");
        if (this.props.toggler === "parent") {
            // Add parent click listener to handle toggling
            useEffect(
                () => {
                    const onClick = (ev) => {
                        if (this.el.contains(ev.target)) {
                            // ignore clicks inside the dropdown
                            return;
                        }
                        this.toggle();
                    };
                    this.el.parentElement.addEventListener("click", onClick);
                    return () => {
                        this.el.parentElement.removeEventListener("click", onClick);
                    };
                },
                () => []
            );

            // Position menu relatively to parent element
            usePosition(() => this.el.parentElement, positioningOptions);
        } else {
            // Position menu relatively to inner toggler
            const togglerRef = useRef("togglerRef");
            usePosition(() => togglerRef.el, positioningOptions);
        }
    },
    /**
     * @override
     */
    onTogglerClick() {
        var self = this;
        const dropdownEl = this.el.parentElement.querySelectorAll('.show');
        const isSearch = $(this.el.parentElement).hasClass('o_search_options');
        dropdownEl.forEach(function(item) {
            if (!document.body.classList.contains('modal-open') && isSearch && item.querySelector('.dropdown-menu')) {
                var button = item.querySelector('button');
                button.click();
            }
        });
        this._super(...arguments);
    },
    /**
     * @override
     */
    onWindowClicked(ev) {
        if (document.body.classList.contains('modal-open')) {
            const dropdownEl = document.querySelector('.modal-body .o_dropdown_ejad.show')
            var button = dropdownEl && dropdownEl.querySelector('button');
            // Close if we clicked outside the dropdown, or outside the parent
            if (button && !button.contains(ev.target) && !ev.target.classList.contains('o_input') &&
                !ev.target.classList.contains('custom-control-label') &&
                !ev.target.classList.contains('custom-control-input') && !ev.target.classList.contains('focus')) {
                button.click();
                $(dropdownEl).removeClass('show');
                $(dropdownEl.querySelector('.o-dropdown--menu')).removeClass('d-block');
            }
        } else {
            this._super(...arguments);
        }
    }
});