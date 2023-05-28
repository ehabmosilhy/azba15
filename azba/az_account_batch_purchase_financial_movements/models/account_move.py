# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"
    batch_purchase_financial_id = fields.Many2one('batch.purchase', string="Batch Purchase Financial")
    purchase_delegate_financial_id = fields.Many2one('hr.employee', string="Delegate Financial")


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    note = fields.Text()
