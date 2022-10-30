odoo.define('ehab_backend_theme.Breadcrumb', function(require) {
    "use strict";

    var config = require('web.config');
    var core = require('web.core');
    var relational_fields = require('web.relational_fields');
    var Qweb = core.qweb;

    relational_fields.FieldStatus.include({
        _render: function() {
            var self = this;
            if (config.device.isMobile) {
                var state_info = _.findWhere(self.status_information, { selected: true });
                this.$el.html(Qweb.render("Breadcrumb.mobile", {
                    selection: self.status_information,
                    state_info: state_info,
                    clickable: self.isClickable,
                }));
            } else {
                return this._super.apply(this, arguments);
            }
        },
    });
});