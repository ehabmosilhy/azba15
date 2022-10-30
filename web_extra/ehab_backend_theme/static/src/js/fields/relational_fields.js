odoo.define('ehab_backend_theme.RelationalFields', function(require) {
    "use strict";

    const config = require('web.config');
    if (!config.device.isMobile) {
        return;
    };

    var relational_fields = require('web.relational_fields');

    relational_fields.FieldMany2One.include({

        _getSearchCreatePopupOptions: function(view, ids, context, dynamicFilters) {
            var options = this._super.apply(this, arguments);
            return $.extend(options, { selectionMode: true });
        },

        _onInputClick: function() {
            return this._searchCreatePopup("search", false, {}, undefined);
        },

    });
});