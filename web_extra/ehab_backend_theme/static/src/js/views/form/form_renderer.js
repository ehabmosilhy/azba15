// odoo Form view inherit for teb view change and form first panel create.
odoo.define('ehab_backend_theme.FormRenderer', function(require) {
    "use strict";

    var __themesDB = require('ehab_backend_theme.ejadWebThemes');
    var FormRenderer = require('web.FormRenderer');
    var FormController = require('web.FormController');
    const config = require('web.config');
    const session = require('web.session');
    const core = require('web.core');
    const Qweb = core.qweb;

    FormController.include({
        _doUpdateActionMenus: function() {
            if (this.hasActionMenus) {
                this.$el.toggleClass('o_open_sidebar', (this.mode === 'readonly' && this.$el.find('.o_cp_action_menus').hasClass('o_drw_in')));
            }
        },
        _update: async function() {
            await this._super(...arguments);
            this._doUpdateActionMenus();
        },
    });

    FormRenderer.include({
        events: _.extend({}, FormRenderer.prototype.events, {
            'click .toggle_btn_chatter': function(e) {
                e.preventDefault();
                this.$el.parent().find('.o_form_view').toggleClass('side_chatter');
            },
        }),
        init: function() {
            this._super.apply(this, arguments);
            this.themeData = __themesDB.get_theme_config_by_uid(session.uid);
        },
        _renderTagSheet: function(node) {
            var $sheet = this._super.apply(this, arguments);
            $sheet.children().not('.o_notebook').not('.o_chatter.oe_chatter').wrapAll($('<div/>', { class: 'o_cu_panel' }));
            return $sheet;
        },
        _renderTabHeader_new: function(page, page_id) {
            var $a = $('<a>', {
                disable_anchor: 'true',
                role: 'tab',
                text: page.attrs.string,
            }).click(function() {
                $(this).parent('li')
                    .toggleClass("ad_close");
            });
            return $('<li>').append($a);
        },
        _renderTagNotebook: function(node) {
            var self = this;
            if (this.themeData && this.themeData.tab_type === 'vertical_tabs') {
                var $headers = $('<ul class="panel-ul" role="tablist">');
                var autofocusTab = -1;
                // renderedTabs is used to aggregate the generated $headers and $pages
                // alongside their node, so that their modifiers can be registered once
                // all tabs have been rendered, to ensure that the first visible tab
                // is correctly activated
                var renderedTabs = _.map(node.children, function(child, index) {
                    var pageID = _.uniqueId('notebook_page_');
                    var $header = self._renderTabHeader_new(child, pageID);
                    var $page = self._renderTabPage(child, pageID);
                    $header.append($page);
                    if (self.themeData.tab_configration === "close_tabs") {
                        $header.addClass("ad_close")
                    }
                    if (autofocusTab === -1 && child.attrs.autofocus === 'autofocus') {
                        autofocusTab = index;
                    }
                    self._handleAttributes($header, child);
                    $headers.append($header);
                    return {
                        $header: $header,
                        $page: $page,
                        node: child,
                    };
                });
                if (renderedTabs.length) {
                    var tabToFocus = renderedTabs[Math.max(0, autofocusTab)];
                    tabToFocus.$header.addClass('active');
                    tabToFocus.$page.addClass('active');
                }
                // register the modifiers for each tab
                _.each(renderedTabs, function(tab) {
                    self._registerModifiers(tab.node, self.state, tab.$header, {
                        callback: function(element, modifiers) {
                            // if the active tab is invisible, activate the first visible tab instead
                            if (modifiers.invisible && element.$el.hasClass('active')) {
                                element.$el.removeClass('active');
                                tab.$page.removeClass('active');
                                var $firstVisibleTab = $headers.find('li:not(.o_invisible_modifier):first()');
                                $firstVisibleTab.addClass('active');
                            }
                        },
                    });
                });
                var $notebook = $('<div class="o_notebook">').append($headers);
                $notebook[0].dataset.name = node.attrs.name || '_default_';
                this._registerModifiers(node, this.state, $notebook);
                this._handleAttributes($notebook, node);
                return $notebook;
            } else {
                return this._super.apply(this, arguments);
            }
        },
        _updateView: function() {
            this._super.apply(this, arguments);
            var self = this;
            if (this.$el.find('.o_FormRenderer_chatterContainer').length) {
                this.$el.prepend('<div class="toggle_btn_chatter"><i class="fa fa-comments"/></div>')
            }
            _.each(this.allFieldWidgets[this.state.id], function(widget) {
                var idForLabel = self.idsForLabels[widget.name];
                var $widgets = self.$('.o_field_widget[name=' + widget.name + ']');
                var $label = idForLabel ? self.$('label[for=' + idForLabel + ']') : $();
                $label = $label.eq($widgets.index(widget.$el));
                if (widget.field.help) {
                    $label.addClass('o_label_help');
                }
            });
        },
        _renderHeaderButtons: function(node) {
            if (config.device.isMobile || (config.device.size_class < config.device.SIZES.SM)) {
                var $buttonGroups = $();

                var children = _.filter(node.children, { tag: 'button' });
                var children_buttons = _.map(children, this._renderHeaderButton.bind(this));
                var $visibleBtn = _.reject(children_buttons, function($b) { return $b.hasClass('o_invisible_modifier'); });

                if ($visibleBtn.length > 0) {
                    $buttonGroups = $(Qweb.render('ButtonGroup'));
                    _.each($visibleBtn, function($btn) {
                        $buttonGroups.find('.dropdown-menu').append($('<li>').append($btn));
                    });
                }
                return $buttonGroups;
            } else {
                return this._super.apply(this, arguments);
            }
        },

        /*
         * Disabled autofocus in responsive (mobile view).
         */
        autofocus: function() {
            if (config.device.isMobile) { return; }
            return this._super.apply(this, arguments);
        },
    });
});