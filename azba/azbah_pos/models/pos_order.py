# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from uuid import uuid4
import pytz

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'
    invoice_name = fields.Char(related='account_move.name')

    # def _export_for_ui(self, order):
    #     data = super(PosOrder, self)._export_for_ui(order)
    #     data['lines'][0][2]['invoice_name'] = order.invoice_name
    #     data['lines'][0][2]['customer_note'] = order.invoice_name
    #     return data
