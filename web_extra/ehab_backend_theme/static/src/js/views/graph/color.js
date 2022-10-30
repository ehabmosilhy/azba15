/** @odoo-module **/

import { COLORS } from "@web/views/graph/colors";
const __themesDB = require('ehab_backend_theme.ejadWebThemes');
const session = require('web.session');
const userTheme = __themesDB.get_theme_config_by_uid(session.uid);
const _isValidHex = function(hexString) { return /^#[0-9A-F]{6}$/i.test(hexString); };
const invertColor = function(hexTripletColor) {
    var color = hexTripletColor;
    color = color.substring(1); // remove #
    color = parseInt(color, 16); // convert to integer
    color = 0xFFFFFF ^ color; // invert three bytes
    color = color.toString(16); // convert to hex
    color = ("000000" + color).slice(-6); // pad with leading zeros
    color = "#" + color; // prepend #
    return color;
}
const THEME_COLORS = _.uniq(_.filter(_.values(userTheme), function(value) { return _isValidHex(value); }));
const ALL_COLORS = _.union(THEME_COLORS, COLORS);

for (let i = 0; i <= ALL_COLORS.length; i++) {
    if (ALL_COLORS[i]) {
        if (userTheme.mode === "night_mode_on") {
            COLORS[i] = invertColor(ALL_COLORS[i]);
        } else {
            COLORS[i] = ALL_COLORS[i];
        }
    }
}