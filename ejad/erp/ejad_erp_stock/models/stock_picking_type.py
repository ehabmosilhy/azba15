# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = 'stock.picking.type'
    _description = 'Stock Picking Type'
    _inherit = ['stock.picking.type']
    _order = 'name'

    is_quality_check = fields.Boolean('Is Quality Check')
