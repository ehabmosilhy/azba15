/** @odoo-module **/

import { WebClient } from "@web/webclient/webclient";
import { useService } from "@web/core/utils/hooks";
import { CustiomizeMenuBar } from "./menubar";
const { hooks } = owl;



export class WebClientCustomize extends WebClient {
    setup() {
        super.setup();
        this.CustomMenu = useService("custom_menu");
    }
    _loadDefaultApp() {
        return this.CustomMenu.toggle('load_default');
    }
}

WebClientCustomize.components = { ...WebClient.components, NavBar: CustiomizeMenuBar };