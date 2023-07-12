# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    batch_purchase_sarf_moshtarayat_id = fields.Many2one('batch.purchase', string="Batch Purchase")

