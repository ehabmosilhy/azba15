# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"
    batch_purchase_financial_id = fields.Many2one(related='purchase_order_id.batch_purchase_sarf_moshtarayat_id', string="Batch Purchase",
                                        store=True)
