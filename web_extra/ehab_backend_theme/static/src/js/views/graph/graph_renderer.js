/** @odoo-module **/

import { GraphRenderer } from "@web/views/graph/graph_renderer";
const __themesDB = require('ehab_backend_theme.ejadWebThemes');
const session = require('web.session');
const userTheme = __themesDB.get_theme_config_by_uid(session.uid);
import { patch } from 'web.utils';

patch(GraphRenderer.prototype, '@ehab_backend_theme/static/src/js/views/graph/graph_renderer.js', {
    renderChart() {
        if (userTheme.mode === "night_mode_on") {
            Chart.defaults.global.defaultFontColor = '#f3f3f3';
            Chart.defaults.scale.gridLines.color = '#636363';
        }
        this._super(...arguments);
    },
});