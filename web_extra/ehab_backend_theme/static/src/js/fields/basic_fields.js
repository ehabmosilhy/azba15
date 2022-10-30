odoo.define("ehab_backend_theme.DashboardGraph", function(require) {
    'use strict';
    var basic_fields = require('web.basic_fields');
    var JournalDashboardGraph = basic_fields.JournalDashboardGraph;

    var __themesDB = require('ehab_backend_theme.ejadWebThemes');
    const _isValidHex = function(hexString) { return /^#[0-9A-F]{6}$/i.test(hexString); };
    const THEME_COLORS = _.uniq(_.filter(_.values(__themesDB.default_web_theme), function(value) { return _isValidHex(value); }));

    JournalDashboardGraph.include({
        /**
         * @override
         */
        _getLineChartConfig: function() {
            var borderColor = this.data[0].is_sample_data ? THEME_COLORS[0] : THEME_COLORS[1];
            var backgroundColor = this.data[0].is_sample_data ? THEME_COLORS[0] : THEME_COLORS[1];
            var res = this._super.apply(this, arguments);
            res.data.datasets = [{
                data: this.data[0].values,
                fill: 'start',
                label: this.data[0].key,
                backgroundColor: backgroundColor,
                borderColor: borderColor,
                borderWidth: 2,
            }]
        },
        /**
         * @override
         */
        _getBarChartConfig: function() {
            var data = [];
            var labels = [];
            var backgroundColor = [];

            this.data[0].values.forEach(function(pt) {
                data.push(pt.value);
                labels.push(pt.label);
                var color = pt.type === 'past' ? THEME_COLORS[0] : (pt.type === 'future' ? THEME_COLORS[1] : THEME_COLORS[2]);
                backgroundColor.push(color);
            });
            var res = this._super.apply(this, arguments);
            res.data.datasets = [{
                data: data,
                fill: 'start',
                label: this.data[0].key,
                backgroundColor: backgroundColor,
            }]
            return res;
        },
    })
});