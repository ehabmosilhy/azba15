/** @odoo-module **/

import { ControlPanel } from "@web/search/control_panel/control_panel";
import { SearchPanel } from "@web/search/search_panel/search_panel";
import { patch } from "@web/core/utils/patch";
import { Model, useModel } from "web.Model";

const { useExternalListener, useState, useSubEnv } = owl.hooks;
const { Portal } = owl.misc;
const STICKY_CLASS = "o_mobile_sticky";

patch(ControlPanel.prototype, "SearchPanel.MobileView", {
    setup() {
        this._super();

        this.state = useState({
            visibleSearch: false,
        });
    },
});
patch(SearchPanel.prototype, '@ehab_backend_theme/js/views/search_panel_mobile.js', {
    setup() {
        useSubEnv({ searchModel: this.props.searchModel });
        this.state = useState({
            visibleSearch: false,
        });
        this.model = useModel("searchModel");
        this._super(...arguments);
    },
});
SearchPanel.components["Portal"] = Portal;
ControlPanel.components["Portal"] = Portal;