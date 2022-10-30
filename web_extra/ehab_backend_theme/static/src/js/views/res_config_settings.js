odoo.define('ehab_backend_theme.settings', function(require) {
    "use strict";

    var BaseSettingRenderer = require('base.settings');
    var session = require('web.session');
    var __themesDB = require('ehab_backend_theme.ejadWebThemes');

    BaseSettingRenderer.Renderer.include({
        init: function() {
            this._super.apply(this, arguments);
            this.meniIcon = true;
        },
        willStart: function() {
            return Promise.all([this._getMenuIconType(), this._super.apply(this, arguments)]);
        },
        _getMenuIconType: function() {
            var themeData = __themesDB.get_theme_config_by_uid(session.uid);
            this.meniIcon = themeData.base_menu_icon;
        },
        start: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                self.$el.parents('.o_content').addClass('oe_base_settings');
            });
        },
        fileExists: function(filename) {
            filename = filename.trim();
            var response = jQuery.ajax({
                url: filename,
                type: 'HEAD',
                async: false
            }).status;
            return (response == "200");
        },
        _getAppIconUrl: function(module) {
            var path;
            var custom_icon_path = '';
            if (this.meniIcon === 'base_icon') {
                custom_icon_path = "/base/static/description/";
                path = "/" + module + "/static/description/icon.png";
            } else if (this.meniIcon === '2d_icon') {
                custom_icon_path = '/ehab_backend_theme/static/src/img/menu_2d/';
                if (this.fileExists(custom_icon_path + module + '.png')) {
                    path = custom_icon_path + module + ".png"
                } else {
                    path = custom_icon_path + "/custom.png";
                    if (this.fileExists("/" + module + "/static/description/icon.png")) {
                        path = "/" + module + "/static/description/icon.png";
                    }
                }
            } else if (this.meniIcon === '3d_icon') {
                custom_icon_path = '/ehab_backend_theme/static/src/img/menu/';
                if (this.fileExists(custom_icon_path + module + '.png')) {
                    path = custom_icon_path + module + ".png"
                } else {
                    path = custom_icon_path + "/custom.png";
                    if (this.fileExists("/" + module + "/static/description/icon.png")) {
                        path = "/" + module + "/static/description/icon.png";
                    }
                }
            }
            else if(this.meniIcon === 'flat_icon'){
                custom_icon_path = '/ehab_backend_theme/static/src/img/menu_flat/';
                if(this.fileExists(custom_icon_path + module+'.png')){
                    path= custom_icon_path + module+".png"
                }else{
                    path = custom_icon_path +"/custom.png";
                    if(this.fileExists("/"+module+"/static/description/icon.png")){
                        path = "/"+module+"/static/description/icon.png";
                    }
                }
            }
            else if(this.meniIcon === 'colors_icon'){
                custom_icon_path = '/ehab_backend_theme/static/src/img/menu_colors/';
                if(this.fileExists(custom_icon_path + module+'.png')){
                    path= custom_icon_path + module+".png"
                }else{
                    path = custom_icon_path +"/custom.png";
                    if(this.fileExists("/"+module+"/static/description/icon.png")){
                        path = "/"+module+"/static/description/icon.png";
                    }
                }
            }
            return module === "general_settings" ? custom_icon_path + "/settings.png" : path;
        },
    });
});