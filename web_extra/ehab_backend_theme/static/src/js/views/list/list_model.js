odoo.define('ehab_backend_theme.ListModel', function(require) {
    "use strict";

    var ListModel = require('web.ListModel');
    var rpc = require('web.rpc');

    var ABTListModel = ListModel.include({
        __get: function() {
            var result = this._super.apply(this, arguments);
            var dp = result && this.localData[result.id];
            if (dp) {
                if (dp.attachmentsData) {
                    result.attachmentsData = $.extend(true, {}, dp.attachmentsData);
                }
                if (dp.nbAttahments) {
                    result.nbAttahments = $.extend(true, {}, dp.nbAttahments);
                }
                if (dp.displayDensity) {
                    result.displayDensity = $.extend(true, {}, dp.displayDensity);
                }
            }
            return result;
        },
        _load: function(dataPoint, options) {
            var def = Promise.resolve();
            const _super = this._super.bind(this, dataPoint, options);
            if (dataPoint) {
                def = this._loadAttachemts(dataPoint);
            };

            return def.then(_super);
        },
        _loadAttachemts: function(dataPoint) {
            return rpc.query({
                model: 'ir.attachment',
                method: 'get_attachments',
                args: [dataPoint.model, dataPoint.domain, dataPoint.context]
            }).then(function(record) {
                _.extend(dataPoint, record);
                return record;
            });
        }
    });
    return ABTListModel;
});