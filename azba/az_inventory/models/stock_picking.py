# -*- coding: utf-8 -*-

from odoo import models, fields

ACCOUNT_DOMAIN = "['&', '&', '&', ('deprecated', '=', False), ('internal_type','=','other'), ('company_id', '=', current_company_id), ('is_off_balance', '=', False)]"

class StockPiciking(models.Model):
    _inherit = "stock.move"
    property_account_expense_categ_id = fields.Many2one('account.account', company_dependent=True,
                                                        string="Expense Account",
                                                        domain=ACCOUNT_DOMAIN,
                                                        help="The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense (Cost of Goods Sold account) is recognized at the customer invoice validation.")