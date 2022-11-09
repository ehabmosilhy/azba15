# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        pos_order = self.env['pos.order'].search([('name', '=', res.ref)])
        if pos_order:
            pos_order.invoice_id = res.highest_name
        return res
