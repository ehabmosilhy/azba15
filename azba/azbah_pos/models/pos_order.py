# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
from functools import partial
from itertools import groupby

import psycopg2
import pytz
import re

from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_round, float_repr, float_compare
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from odoo.osv.expression import AND
import base64

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        if order_fields['lines']: #[[0, 0, {'qty': 5, 'price_unit': 1, 'price_subtotal': 5, 'price_subtotal_incl': 5.75, 'discount': 0, 'product_id': 6, 'tax_ids': [[6, False, [1]]], 'id': 17, 'pack_lot_ids': [], 'full_product_name': 'قوارير ابيض مع المياة', 'name': 'Shop/0014'}]]
            order_fields['to_invoice'] = True
        else:
            order_fields['to_invoice'] = False
        return order_fields
