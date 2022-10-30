# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MandatePayment(models.TransientModel):
    _name = 'bank.letter.wizard'
    _description = 'Bank Letter Wizard'


    date = fields.Date('التاريخ', default=fields.Date.context_today, required=True)
    journal_id = fields.Many2one('account.journal', string='طريقة السداد', required=True,
                                 domain=['|', ('type', '=', 'bank'), ('type', '=', 'cash')])
    amount = fields.Monetary('المبلغ')
    employee_id = fields.Many2one('hr.employee')
    employee_name = fields.Char(string='اسم المستفيد')
    report = fields.Char(string='البيان')
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', store=True, string="Currency")
    amount_text = fields.Char(compute='_compute_amount_to_text')
    bank_id = fields.Many2one(related='journal_id.bank_id')
    bank_name_id = fields.Char(related='bank_id.name')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.employee_name = self.employee_id.name


    @api.depends('amount')
    def _compute_amount_to_text(self):

        self.amount_text = self.env.user.company_id.currency_id.amount_to_text(self.amount)


    def _compute_currency(self):
        self.currency_id = self.env.user.company_id.currency_id.id

    
    def print_bank_letter(self):
        data = {}
        data['form'] = self.read()
        print("  DDD   ", data)
        return self.env.ref('ejad_erp_hr.action_bank_letter_report').report_action(self, data=data)

        # return {'type': 'ir.actions.act_window_close'}
