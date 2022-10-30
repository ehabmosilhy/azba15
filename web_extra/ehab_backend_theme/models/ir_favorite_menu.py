# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import api, fields, models


class FavoriteUiMenu(models.Model):
    _name = 'ir.favorite.menu'
    _order = "sequence"
    _description = "Favorite Menu"

    favorite_menu_id = fields.Many2one('ir.ui.menu', string='Favorite Menu',
        required=True, ondelete='cascade')
    theme_icon_data = fields.Binary(string='Web Icon Image', related='favorite_menu_id.theme_icon_data')
    user_id = fields.Many2one('res.users', string='User Name')
    sequence = fields.Integer(string="sequence")
    favorite_menu_xml_id = fields.Char(string="Favorite Menu Xml")
    favorite_menu_action_id = fields.Integer(string="Favorite Menu Action")

    _sql_constraints = [
        ('favorite_menu_user_uniq', 'unique (favorite_menu_id,user_id)', "Duplicate favorite menu is not allow for same user!")
    ]

    @api.model
    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('ir.favorite.menu') or 0
        return super(FavoriteUiMenu, self).create(vals)

    @api.model
    def get_favorite_menus(self):
        visibleMenus = self.search([('user_id', '=', self.env.user.id)]).mapped('favorite_menu_id')._filter_visible_menus()
        favorite_menus = self.search_read([
            ('favorite_menu_id', 'in', visibleMenus.ids), ('user_id', '=', self.env.user.id)],
            ['favorite_menu_id', 'user_id', 'sequence', 'favorite_menu_xml_id', 'favorite_menu_action_id', 'theme_icon_data'])
        return favorite_menus

    @api.model
    def del_fev_menu(self):
        favorite_menus = self.search([])
        return favorite_menus

