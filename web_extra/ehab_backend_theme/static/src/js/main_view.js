odoo.define('ehab_backend_theme.General', function(require) {
    "use strict";

    var config = require('web.config');
    require('web.dom_ready');

    (function() {
        const $body = jQuery("body");
        //Mobile view detect
        if (config.device.isMobile) {
            $body.addClass('ad_mobile ad_full_view');
        };

        //$(document).width() <= 991
        if (config.device.size_class < config.device.SIZES.LG) {
            $body.addClass('ad_full_view');
        };
    })();

});