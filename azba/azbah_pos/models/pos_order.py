# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pytz

from odoo import api, fields, models, tools, _


class PosOrder(models.Model):
    _inherit = 'pos.order'
    invoice_name = fields.Char(related='account_move.name')

    def _export_for_ui(self, order):
        timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        res = super()._export_for_ui(order=order)
        if res:
            res.update({
                'order_date': order.date_order.astimezone(timezone),
                'invoice_number': order.account_move and order.account_move.name or ""
            })
        return res