/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { useService } from "@web/core/utils/hooks";
const { hooks, useState } = owl;
const core = require('web.core');
const config = require('web.config');
const { useListener } = require('web.custom_hooks');
import { registry } from "@web/core/registry";
const { useExternalListener } = hooks;


export class CustiomizeMenuBar extends NavBar {
    setup() {
        super.setup();
        this.CustomMenu = useService("custom_menu");
        this.menuService = useService("menu");
        this.debug = config.isDebug() ? '?debug' : '';
        this.isTouchDevice = config.device.touch;
        this.state = useState({
            favoriteMenuNameById: {},
            menus: [],
        });
    }
    constructor() {
        super(...arguments);
        core.bus.on('click_favorite_menu', this, this._getFavMenuData);
        useExternalListener(window, "click", this._getfullScreen);
    }
    async willStart() {
        await this._getFavMenuData();
        return super.willStart();
    }
    _getfullScreen(ev) {
        if (this.isTouchDevice && !this.el.contains(ev.target) &&
            !document.body.classList.contains('ad_full_view')) {
            $('body').toggleClass('ad_full_view');
        }
    }
    async _getFavMenuData() {
        var self = this;
        var favorites = await this.env.services.orm.call("ir.favorite.menu", "get_favorite_menus");
        if (favorites) {
            favorites.forEach(function(menu) {
                self.state.favoriteMenuNameById[menu.favorite_menu_id[0]] = menu.favorite_menu_id[1];
            });
            self.state.menus = favorites.map(function(menu) {
                return _.extend(menu, {
                    theme_icon_data: ('data:image/png;base64,' + menu.theme_icon_data).replace(/\s/g, ""),
                    actionID: menu.favorite_menu_action_id,
                    xmlid: menu.favorite_menu_xml_id,
                    parents: "",
                    appID: menu.favorite_menu_id[0],
                    action() {
                        $('.o_menu_systray').removeClass('show');
                        self.menuService.selectMenu(menu);
                    },
                });
            });
        }
    }
    async render() {
        await super.render();
        var self = this;
        const favorite_menu = this.el.querySelector('.oe_apps_menu');
        if (favorite_menu) {
            $(favorite_menu).sortable({
                items: "> .oe_favorite",
                axis: 'y',
                stop: (event, ui) => {
                    $(favorite_menu).children().each(function(index) {
                        var vals = {};
                        var menu_id = $(this).data('id');
                        vals['sequence'] = index;
                        vals['favorite_menu_id'] = $(this).data('menu-id');
                        self.env.services.orm.call("ir.favorite.menu", "write", [
                            [menu_id], vals
                        ]);
                    });
                },
            });
        }
    }
    onOpenMenu() {
        return this.state.menus;
    }
    OpenMenu(menu) {
        this.menuService.setCurrentMenu(menu.appID);
        menu.action();
    }
    onFullViewClicked() {
        $('body').toggleClass('ad_full_view');
    }
    onFullScreen() {
        document.fullScreenElement && null !== document.fullScreenElement || !document.mozFullScreen &&
            !document.webkitIsFullScreen ? document.documentElement.requestFullScreen ? document.documentElement.requestFullScreen() :
            document.documentElement.mozRequestFullScreen ? document.documentElement.mozRequestFullScreen() :
            document.documentElement.webkitRequestFullScreen && document.documentElement.webkitRequestFullScreen(Element.ALLOW_KEYBOARD_INPUT) :
            document.cancelFullScreen ? document.cancelFullScreen() :
            document.mozCancelFullScreen ? document.mozCancelFullScreen() :
            document.webkitCancelFullScreen && document.webkitCancelFullScreen()
    }
}
CustiomizeMenuBar.template = "ehab_backend_theme.CustomMenu";
registry.category("actions").add("fav_menu_item", CustiomizeMenuBar);