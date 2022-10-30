odoo.define('ehab_backend_theme.kanban_column_quick_create', function(require) {
    "use strict";

    const config = require('web.config');
    const KanbanColumnQuickCreate = require('web.kanban_column_quick_create');

    KanbanColumnQuickCreate.include({

        init: function(parent, options) {
            this._super(...arguments);
            this.isMobile = config.device.isMobile;
        },

        /**
         * Override to only update for desktop views
         *
         * @override
         */
        _cancel: function() {
            if (!this.folded) {
                this.$input.val('');
                if (!this.isMobile) {
                    this.folded = true;
                    this._update();
                }
            }
        },
    });

});