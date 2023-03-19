# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _
from odoo.tools.misc import format_date

from dateutil.relativedelta import relativedelta
from itertools import chain


class PosOrder(models.Model):
    _inherit = "pos.order"
    invoice_id = fields.Integer(related="account_move.id")
