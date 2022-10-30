/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { useService } from "@web/core/utils/hooks";
const { Component, hooks } = owl;

export class FavoriteMenu extends Component {
    setup() {
        super.setup();

        this.CustomMenu = useService("custom_menu");
    }
}
FavoriteMenu.template = "web.NavBar.favroitMenu";