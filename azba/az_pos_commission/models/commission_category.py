# -*- coding: utf-8 -*-

from odoo import fields, models


class CommissionProduct(models.Model):
    _name = 'az.commission.category'
    _description = 'Commission Categories'
    name = fields.Char("اسم الفئة")
    amount = fields.Float("العمولة")