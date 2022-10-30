# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.

from odoo import http
from odoo.addons.web.controllers.main import *
from odoo.http import request


class MenuSearch(http.Controller):

    @http.route('/all/menu/search', auth='user', type='json')
    def all_visible_menu(self):
        all_menu_ids = request.env['ir.ui.menu'].search([('action', '!=', False)])
        menu_ids = []
        for menu in all_menu_ids:
            parent_path = menu.parent_path
            parent_menu_list = list(map(int, parent_path.split('/')[:-1]))
            parent_menu_ids = request.env['ir.ui.menu'].browse(parent_menu_list)
            if len(parent_menu_list) == len(parent_menu_ids._filter_visible_menus()):
                menu_ids.append(menu.id)
        menu_datas = request.env['ir.ui.menu'].search_read([
            ('id', 'in', menu_ids),
            ('action', '!=', False)],
            ['name', 'action', 'complete_name','parent_path'])
        return menu_datas
