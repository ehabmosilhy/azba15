# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"
    purchase_order_id = fields.Many2one('purchase.order', string="Purchase Order")
    batch_purchase_id = fields.Many2one(related='purchase_order_id.batch_purchase_id', string="Batch Purchase", store=True)
    purchase_delegate_id = fields.Many2one('hr.employee', string="Delegate")
