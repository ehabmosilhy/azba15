# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _name = 'product.category'
    _description = 'Product Category'
    _inherit = ['product.category']
    _order = 'name'

    is_related_revenue = fields.Boolean('هل الفئة تتبع للإيرادات')



