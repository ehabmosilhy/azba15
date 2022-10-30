odoo.define('ehab_backend_theme.DashboardCustomizeTheme', function(require) {
    "use strict";

    var __themesDB = require('ehab_backend_theme.ejadWebThemes');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var Dialog = require('web.Dialog');
    var session = require('web.session');
    var SystrayMenu = require('web.SystrayMenu');
    var _t = core._t;

    var fields = {
        'leftbar_color': 'LeftBar',
        'menu_color': 'Menu',
        'buttons_color': 'Button',
        'button_box': 'Button Box',
        'heading_color': 'Heading',
        'label_color': 'Label',
        'lael_value_color': 'Label Value',
        'link_color': 'Link Color',
        'panel_title_color': 'Panel Title',
        'tooltip_color': 'Tooltip',
        'border_color': 'Border',
        'font_type_values': 'Font Value',
        'base_menu': 'Menu Configration',
        'base_form_tabs': 'Form Tab',
        'tab_configration': 'Tab Configration',
        'base_menu_icon': 'Icon Value',
        'mode': 'Mode',
    };

    var CustomizeThemeDialog = Dialog.extend({
        dialog_title: _t('Customize Theme'),
        template: "CustomizeTheme",
        events: {
            'click .o_add_theme': '_onClickAddRecord',
            'click ul.oe_theme_colorpicker li .o_view': '_onClickSelectTheme',
            'click ul.oe_theme_colorpicker li .o_remove': '_onClickRemoveTheme',
            'click .o_radio_input': '_ontabClickOption',
            'click .nav-link': '_ontabClickOption',
        },
        init: function(parent, result, themeData) {
            var self = this;
            this.ejadThemes = result;
            this.parent = parent;
            this.themeData = themeData;
            this.theme_id = themeData.id || 0;
            this.form_values = {};
            this.group_system = parent.group_system;
            $('body').addClass('open_customize_theme');
            this._super(parent, {
                title: _t('Customize Theme'),
                buttons: [{
                    text: _t('Apply'),
                    classes: 'btn-primary',
                    click: function() {
                        self._onClickSaveTheme();
                    },
                }, {
                    text: _t('Cancel'),
                    close: true,
                }],
            });
        },
        start: function() {
            var self = this;
            this.invalidFields = [];
            var themeData;

            this.$('.o_colorpicker').each(function() {
                $(this).minicolors({
                    control: 'hue',
                    inline: false,
                    letterCase: 'lowercase',
                    opacity: false,
                    theme: 'bootstrap'
                });
            });
            if (!_.isEmpty(this.ejadThemes)) {
                this.current_theme = _.findWhere(this.ejadThemes, { selected: true });
                if (!_.isUndefined(this.current_theme)) {
                    self._setSelectedTheme(_.findWhere(self.ejadThemes, { id: self.current_theme.id }), true);
                }
            }
            if (self.themeData && self.themeData.mode === 'night_mode_on') {
                self.$el.addClass('night_mode_on');
            }
            return this._super.apply(this, arguments);
        },
        close: function() {
            this.parent.customizeDialog = false;
            $('body').removeClass('open_customize_theme');
            this._super.apply(this, arguments);
        },
        destroy: function(options) {
            this.parent.customizeDialog = false;
            $('body').removeClass('open_customize_theme');
            this._super.apply(this, arguments);
        },
        _onClickAddRecord: function() {
            this.$el.addClass('o_new_record');
            this.$('.o_control_form').find('input.minicolors-input').minicolors('value', '');
            this.$('.o_breadcrumb_form').find('input').minicolors('value', '');
        },
        _setSelectedTheme: function(result, init) {
            var self = this;
            this.$el.removeClass('o_new_record');
            _.each(result, function(value, field) {
                if (!_.contains(['font_type_values', 'base_menu', 'base_form_tabs', 'tab_configration', 'mode', 'base_menu_icon'], field)) {
                    self.$('input[name=' + field + ']').minicolors('value', value);
                } else {
                    if (!_.contains(['base_form_tabs', 'font_type_values', 'base_menu', 'tab_configration', 'mode'], field)) {
                        self.$('input[value="' + value + '"]').prop("checked", true);
                    } else if (init && !_.isEmpty(self.themeData)) {
                        self.$('input[value="' + self.themeData.tab_type + '"]').prop("checked", true);
                        self.$('input[value="' + self.themeData.tab_configration + '"]').prop("checked", true);
                        self.$('input[value="' + self.themeData.base_menu + '"]').prop("checked", true);
                        self.$('input[value="' + self.themeData.font_type_values + '"]').prop("checked", true);
                        self.$('input[value="' + self.themeData.mode + '"]').prop("checked", true);
                    }
                    if (self.themeData.tab_type === 'vertical_tabs') {
                        self.$el.find('.tab_configration_data').show();
                    } else if (self.themeData.tab_type === 'horizontal_tabs') {
                        self.$el.find('.tab_configration_data').hide();
                    }
                }
            })
            if (init) { this._ontabClickOption(result); };
        },
        _removeTheme: function($li, res_id) {
            var self = this;
            self._rpc({
                model: 'ir.web.theme',
                method: 'remove_and_settingup_default',
                args: [parseInt(res_id, 10)],
            }).then(function(need_to_reload) {
                $li.remove();
                self.displayNotification({ title: _t('"Sucsess"'), message: _t("Theme removed successfully.") });
                if (need_to_reload) {
                    self.close(true);
                    location.reload();
                }
            })
        },
        _onClickSelectTheme: function(e) {
            var self = this;
            this.$el.find('ul li').removeClass('selected');
            $(e.currentTarget).parents('li').addClass('selected');
            var res_id = $(e.currentTarget).parents('li').find('span').data('id');
            if (res_id !== 0) {
                self._setSelectedTheme(_.findWhere(self.ejadThemes, { id: res_id }), false);
            }
        },
        _onClickRemoveTheme: function(e) {
            var self = this;
            var $themeLi = $(e.currentTarget).parents('li');
            var res_id = $themeLi.find('span').data('id');
            var res = false;

            var process_unlink = function(confirm) {
                if (confirm) { self._removeTheme($themeLi, res_id); } else {
                    return false;
                };
            };

            if (res_id === self.current_theme.id) {
                process_unlink(confirm(_t("This theme is currently applied, by deleting this theme a default theme will be applied by the system automatically.\n\nDo you want to proceed anyway?")));
            } else {
                process_unlink(confirm(_t("Are you sure want to delete this theme?")));
            };
        },
        _createRecord: function(form_values) {
            return this._rpc({
                model: 'ir.web.theme',
                method: 'create_and_settingup_theme',
                args: [_.defaults(form_values, { ttype: "custom" })],
                kwargs: { context: session.user_context },
            });
        },
        _updateRecord: function(theme_id, form_values) {
            var self = this,
                user_vals = {};
            if (form_values) {
                user_vals = {
                    'tab_type': form_values.base_form_tabs,
                    'tab_configration': form_values.tab_configration,
                    'base_menu': form_values.base_menu,
                    'font_type_values': form_values.font_type_values,
                    'mode': form_values.mode,
                };
            }
            return this._rpc({
                model: 'ir.web.theme',
                method: 'write',
                args: [
                    [theme_id], form_values
                ],
            }).then(function(value) {
                return self._rpc({
                    model: 'res.users',
                    method: 'write',
                    args: [
                        [session.uid], user_vals
                    ],
                })
            });
        },
        _doChangeTheme: function(theme_id) {
            var self = this;
            self.displayNotification({ title: _t('"Sucsess"'), message: _t("Theme customized successfully.") });
            self.close(true);
            location.reload();
            return;
        },
        _onClickSaveTheme: function() {
            var self = this,
                theme_id;
            var form_fields = this.$('.o_control_form').serializeArray();
            _.each(form_fields, function(input) {
                if (input.value !== '') {
                    self.form_values[input.name] = input.value;
                } else if (!self.$el.hasClass('night_mode_on')) {
                    self.invalidFields.push(input.name);
                }
            });
            if (!_.isEmpty(self.invalidFields)) {
                self.invalidFields = [];
                return false;
            } else {
                if (self.$el.hasClass('o_new_record') && !self.$el.hasClass('night_mode_on')) {
                    self._createRecord(self.form_values).then(function(theme_id) {
                        self._doChangeTheme(theme_id);
                    })
                } else {
                    theme_id = this.$el.find('ul li.selected span').data('id');
                    theme_id = theme_id || self.theme_id;
                    if (theme_id && !_.isUndefined(theme_id) && theme_id !== 0) {
                        self._updateRecord(parseInt(theme_id), self.form_values).then(function() {
                            self._doChangeTheme(parseInt(theme_id));
                        })
                    }
                }

            }
            if (self.group_system) {
                self._create_icon(self.form_values);
            }
        },
        _create_icon: function(form_values) {
            var self = this;
            return this._rpc({
                model: 'ir.ui.menu',
                method: 'icon_menu_chnange',
                args: [self.form_values],
            });
        },
        _ontabClickOption: function(event) {
            var self = this;
            var $activetab = $(event.target).closest('.oe_teb_view').attr('value');
            var form_fields = this.$('.o_control_form').serializeArray();
            var imagePath = '/ehab_backend_theme/static/src/img/';
            var $night_mode = _.findWhere(form_fields, { 'name': 'mode' })
            var $tab_data = _.findWhere(form_fields, { 'name': 'base_form_tabs' })
            if ($activetab) {
                var data = _.findWhere(form_fields, { 'name': $activetab });
                self.$el.find('.uc_menu_image').attr('src', imagePath + data["value"] + '.png');
            } else {
                self.$el.find('.uc_menu_image').attr('src', '/ehab_backend_theme/static/src/img/theme_help.png');
            }
            self.$el.find('.tab_configration_data').toggle($tab_data["value"] == 'vertical_tabs');
            self.$el.toggleClass('night_mode_on', $night_mode["value"] == 'night_mode_on');
        },
    });
    var DashboardCustomizeTheme = Widget.extend({
        template: 'DashboardThemeColors',
        events: {
            'click .o_setup_theme': '_onClickSetupTheme'
        },
        init: function(parent) {
            this.parent = parent;
            this.group_system = false;
            this.group_theme_config = false;
            this.customizeDialog = false;
            this.themes = __themesDB.get_themes();
            this.userTheme = __themesDB.get_theme_config_by_uid(session.uid);
            this._super.apply(this, arguments);
        },
        willStart: function() {
            var self = this;
            self.nightMode = this.userTheme.mode || false;
            var GroupSystem = self.getSession().user_has_group('base.group_system').then(function(has_group) {
                self.group_system = has_group;
            });
            var acl = self.getSession().user_has_group('ehab_backend_theme.group_theme_setting_user').then(function(is_theme_access) {
                self.group_theme_config = is_theme_access
            });
            return Promise.all([this._super.apply(this, arguments), GroupSystem, acl]);
        },
        start: function() {
            this._super.apply(this, arguments);
            if (this.nightMode && this.nightMode === 'light_mode_on') {
                $('body').addClass('light_mode_on');
            }
            if (this.nightMode && this.nightMode === 'night_mode_on') {
                $('body').addClass('oe_night_mode');
            }
        },
        _onClickSetupTheme: function(ev) {
            ev.preventDefault();
            var self = this;
            if (!this.customizeDialog) {
                $('.o_menu_systray').hasClass('show') && $('.o_menu_systray').removeClass('show');
                this.customizeDialog = new CustomizeThemeDialog(self, this.themes, this.userTheme).open();
            } else {
                this.customizeDialog.close();
            }
        },
    });
    SystrayMenu.Items.push(DashboardCustomizeTheme);
    return SystrayMenu;
});