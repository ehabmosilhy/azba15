/** @odoo-module **/

import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';

var HelperMenu = Widget.extend({
    name: 'helper_menu',
    template: 'ehab_backend_theme.SystrayHepler',
});

SystrayMenu.Items.push(HelperMenu);
export default HelperMenu;