# -*- coding: utf-8 -*-
from odoo import fields, models,api


class AccountPartnerLedger(models.TransientModel):
    _name = "account.report.partner.ledger"
    _inherit = "account.common.report"

    result_selection = fields.Selection(
        [('customer', 'Receivable Accounts'), ('supplier', 'Payable Accounts'),
         ('customer_supplier', 'Receivable and Payable Accounts')],
        string="Partner's", required=True, default='customer')

    def pre_print_report(self, data):
        data['form'].update(self.read(['result_selection'])[0])
        return data


    amount_currency = fields.Boolean(
        string="With Currency",
        help="It adds the currency column on report if the currency differs "
             "from the company currency.")
    reconciled = fields.Boolean(string='Reconciled Entries')

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled,
                             'amount_currency': self.amount_currency})
        return self.env.ref(
            'az_account_partner_ledger_filter.action_report_partnerledger').report_action(
            self, data=data)
