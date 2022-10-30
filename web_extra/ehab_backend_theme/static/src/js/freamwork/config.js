odoo.define('web.config.customize', function(require) {
    "use strict";

    const config = require('web.config');
    const isTouchDevices = "ontouchstart" in window || "onmsgesturechange" in window;

    if (!isTouchDevices) { return; };

    var medias = [
        window.matchMedia('(max-width: 474px)'),
        window.matchMedia('(min-width: 475px) and (max-width: 575px)'),
        window.matchMedia('(min-width: 576px) and (max-width: 767px)'),
        window.matchMedia('(min-width: 768px) and (max-width: 991px)'),
        window.matchMedia('(min-width: 992px) and (max-width: 1199px)'),
        window.matchMedia('(min-width: 1200px) and (max-width: 1533px)'),
        window.matchMedia('(min-width: 1534px)'),
    ];

    function _getSizeClass() {
        for (var i = 0; i < medias.length; i++) {
            if (medias[i].matches) {
                return i;
            };
        };
    };

    function _updateejadSizeProps() {
        config.device.size_class = _getSizeClass();
        config.device.isMobile = true;
        config.device.bus.trigger('size_changed', config.device.size_class);
    };

    _.invoke(medias, 'addListener', _updateejadSizeProps);
    _updateejadSizeProps();

});