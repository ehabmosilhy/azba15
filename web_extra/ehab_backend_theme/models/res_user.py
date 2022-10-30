# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

import datetime
from odoo import fields, models, api, modules
from odoo.modules import get_module_resource


class ResUsers(models.Model):
    _inherit = 'res.users'

    display_density = fields.Selection([
                ('default', 'Default'),
                ('comfortable', 'Comfortable'),
                ('compact', 'Compact'),
            ], string="Display Density", default='default')
    tab_type = fields.Selection([
                ('horizontal_tabs', 'Horizontal Tabs'),
                ('vertical_tabs', 'Vertical Tabs'),
            ], string="Tab Type", default='horizontal_tabs')
    tab_configration = fields.Selection([
                ('open_tabs','Open Tabs'),
                ('close_tabs','Close Tabs',),
            ], string="Tab Config.", default='open_tabs')
    base_menu =  fields.Selection([
                ('base_menu','Horizontal Menu'),
                ('theme_menu','Vertical Menu'),
            ], string="Menu", default='base_menu')
    font_type_values =  fields.Selection([
                ('roboto','Roboto'),
                ('open_sans','Open Sans'),
                ('alice','Alice'),
                ('abel','Abel'),
                ('montserrat','Montserrat'),
                ('lato','Lato'),
            ], string="Font", default='roboto')
    mode = fields.Selection([
        ('light_mode_on', 'Light'),
        ('night_mode_on', 'Night'),
        ('normal_mode_on', 'Normal'),
        ], string="Mode", default='normal_mode_on')

    @api.model
    def get_users_themes(self):
        return self.search_read([('share', '=', False)], [
            'display_density', 'tab_type', 'tab_configration',
            'base_menu', 'font_type_values', 'mode'
        ])

    def get_module_theme_icon(self, module):
        icon = module + '.png'
        current_theme = self.env['ir.web.theme'].get_current_theme()
        theme_type = self.env['ir.web.theme'].browse(int(current_theme))
        if theme_type.base_menu_icon == '3d_icon':
            iconpath = ['static', 'src', 'img', 'menu', icon]
        elif theme_type.base_menu_icon == '2d_icon':
            iconpath = ['static', 'src', 'img', 'menu_2d', icon]
        elif theme_type.base_menu_icon == 'flat_icon':
            iconpath = ['static', 'src', 'img', 'menu_flat', icon]
        elif theme_type.base_menu_icon == 'colors_icon':
            iconpath = ['static', 'src', 'img', 'menu_colors', icon]
        else:
            return modules.module.get_module_icon(module)
        if modules.module.get_module_resource(module, *iconpath):
            return ('/' + 'ehab_backend_theme' + '/') + '/'.join(iconpath)
        return '/ehab_backend_theme/'  + '/'.join(iconpath)

    @api.model
    def systray_get_activities(self):
        res = super(ResUsers, self).systray_get_activities();
        for resList in res:
            module = self.env[resList['model']]._original_module
            icon = module and self.get_module_theme_icon(module)
            resList['icon'] = icon
        return res