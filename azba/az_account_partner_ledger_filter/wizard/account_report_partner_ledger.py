# -*- coding: utf-8 -*-

from odoo import fields, models,api


class AccountPartnerLedger(models.TransientModel):
    _inherit = "account.report.partner.ledger"

    partner_ids = fields.Many2many('res.partner', 'partner_ledger_res_partner_rel', 'id', 'partner_id', string='Partners')

    def _default_journal_ids(self):
        defo = self.env['account.journal'].search([('id', 'in', [5])])
        return defo

    my_journal_ids = fields.Many2many(
        comodel_name='account.journal',relation="journal_filter_rel",
        string='Journals',
        required=True,
    )
    @api.onchange('my_journal_ids')
    def on_change(self):
        if self.my_journal_ids:
            self.journal_ids = self.my_journal_ids

    @api.model
    def default_get(self, fields_list):
        defaults = super(AccountPartnerLedger, self).default_get(fields_list)
        if 'journal_ids' in fields_list:
            defaults['journal_ids'] = self.env['account.journal'].search([('id', 'in', [5])])
        return defaults


    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'reconciled': self.reconciled, 'amount_currency': self.amount_currency,
                             'partner_ids': self.partner_ids.ids})
        return self.env.ref('az_account_partner_ledger_filter.action_report_partnerledger').report_action(self, data=data)
