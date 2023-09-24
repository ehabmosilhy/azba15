# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    batch_purchase_id = fields.Many2one('batch.purchase', string="Batch Purchase")
    delegate_id = fields.Many2one(related='batch_purchase_id.delegate_id')


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    note = fields.Text()
    account_id = fields.Many2one('account.account', 'Account')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
