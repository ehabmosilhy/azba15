/** @odoo-module **/

import { startWebClient } from "@web/start";
import { WebClientCustomize } from "./webclient/webclient";

var __themesDB = require('ehab_backend_theme.ejadWebThemes');
var session = require('web.session');
// Added Global
window['ejadTheme'] = __themesDB.get_theme_config_by_uid(session.uid);

startWebClient(WebClientCustomize);