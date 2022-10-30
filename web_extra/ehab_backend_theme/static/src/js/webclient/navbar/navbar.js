/** @odoo-module **/
import { browser } from "@web/core/browser/browser";
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from 'web.utils';
import { useService } from "@web/core/utils/hooks";

patch(NavBar.prototype, 'web/static/src/webclient/navbar/navbar.js', {
    setup() {
        this._super();
        this.user = useService("user");
    },
    /**
     * @private
     */
    get userData() {
        const { origin } = browser.location;
        const { userId } = this.user;
        this.source = `${origin}/web/image?model=res.users&field=avatar_128&id=${userId}`;
        return this.source;
    },

    CloseUserMenu() {
        $('.o_menu_systray').removeClass('show');
    }
});