# -*- coding: utf-8 -*-
from odoo import models, fields,api

class BatchPurchaseFinancial(models.Model):
    # _name = "batch.purchase.financial"
    _inherit = 'batch.purchase'

    @api.model
    def create(self, vals_list):
        super(BatchPurchaseFinancial, self).create(vals_list)  # Call parent model's create()