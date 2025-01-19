# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _


class FleetServiceType(models.Model):
    _inherit = 'fleet.service.type'
    
    code = fields.Char(string="الكود Code")

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for service in self:
            service.display_name = f'[{service.code}] {service.name}' if service.code else service.name or ''

    display_name = fields.Char(compute='_compute_display_name', store=True, readonly=False)

    _sql_constraints = [('code_uniq', 'unique (code)', """Code must be unique هذا الكود موجود من قبل!""")]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '[%s] %s' % (rec.code, rec.name)))
        return result