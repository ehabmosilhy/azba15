# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MultiBankLetter(models.TransientModel):
    _name = 'bank.letter.multi.wizard'

    date = fields.Date('التاريخ', default=fields.Date.today(), required=True)
    invoice_id = fields.Many2one('account.invoice.multi.partners', string='invoice multi partners')
    journal_id = fields.Many2one('account.journal', string='طريقة السداد', required=True,
                                 domain=['|', ('type', '=', 'bank'), ('type', '=', 'cash')])
    line_ids = fields.Many2many('account.invoice.multi.partners.line', 'account_invoice_bank_letter_multi_wizard_rel',
                                string='المصروفات')
    bank_id = fields.Many2one(related='journal_id.bank_id')
    bank_account_id = fields.Many2one(related='journal_id.bank_account_id')
    bank_name_id = fields.Char(related='bank_id.name')
    line_number = fields.Integer('lines number', compute='_compute_line_number')
    total_amount = fields.Float('Total Amount', compute='_compute_total_amount')

    @api.depends('line_ids')
    def _compute_line_number(self):
        self.line_number = len(self.line_ids)

    @api.depends('line_ids', 'line_ids.amount')
    def _compute_total_amount(self):
        self.total_amount = sum([x.amount for x in self.line_ids])

    def print_bank_letter(self):
        data = {}
        data['form'] = self.read()
        print("  DDD   ", data)
        return self.env.ref('ejad_erp_account.action_bank_letter_multi_report').report_action(self, data=data)
