# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PayrollBankLetter(models.TransientModel):
    _name = 'bank.letter.payroll.wizard'
    _description = 'Bank Letter Payroll Wizard'

    date = fields.Date('التاريخ', default=fields.Date.context_today, required=True)
    payroll_advice_id = fields.Many2one('hr.payroll.advice', string='إشعار الدفع')
    journal_id = fields.Many2one('account.journal', string='طريقة السداد', required=True,
                                 domain=['|', ('type', '=', 'bank'), ('type', '=', 'cash')])
    line_ids = fields.Many2many('hr.payroll.advice.line', string='مرتب الموظف')
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
        return self.env.ref('ejad_erp_hr.action_bank_letter_payroll_report').report_action(self, data=data)
