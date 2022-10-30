# -*- coding: utf-8 -*-

from datetime import datetime
import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class TrailBalanceReportInherit(models.AbstractModel):
    _inherit = 'account.coa.report'

    def total_accounts(self, accounts):
        total_debit = 0
        total_credit = 0
        total_balance = 0
        for account in accounts:
            total_debit += account['debit']
            total_credit += account['credit']
        dic = {
            'total_debit': total_debit,
            'total_credit': total_credit,
            'total_balance': total_debit - total_credit,
        }
        return dic

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
        display_account = data['form'].get('display_account')
        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        account_res = self.with_context(data['form'].get('used_context'))._get_accounts(accounts, display_account)

        return {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': account_res,
            'total_accounts': self.total_accounts(account_res),

        }


class GeneralLedgerReport(models.AbstractModel):
    _inherit = 'account.general.ledger'

    def total_accounts(self, accounts):
        total_debit = 0
        total_credit = 0
        total_balance = 0
        for account in accounts:
            total_debit += account['debit']
            print(account['debit'])
            print(account['credit'])
            total_credit += account['credit']
        dic = {
            'total_debit': total_debit,
            'total_credit': total_credit,
            'total_balance': total_debit - total_credit,
        }
        return dic

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_ids', []))

        init_balance = data['form'].get('initial_balance', True)
        sortby = data['form'].get('sortby', 'sort_date')
        display_account = data['form']['display_account']
        codes = []
        if data['form'].get('journal_ids', False):
            codes = [journal.code for journal in
                     self.env['account.journal'].search([('id', 'in', data['form']['journal_ids'])])]

        accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        accounts_res = self.with_context(data['form'].get('used_context', {}))._get_account_move_entry(accounts,
                                                                                                       init_balance,
                                                                                                       sortby,
                                                                                                       display_account)
        return {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'Accounts': accounts_res,
            'print_journal': codes,
            'total_accounts': self.total_accounts(accounts_res),

        }
