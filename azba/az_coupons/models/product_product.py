# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from datetime import datetime


class Coupon(models.Model):
    _inherit = 'product.product'

    coupon_paper_count = fields.Integer(string='Coupon Paper Count')