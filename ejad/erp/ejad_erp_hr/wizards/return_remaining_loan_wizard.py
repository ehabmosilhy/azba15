# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EndOfServices(models.TransientModel):
    _name = 'loan.return.remaining.wizard'
    _description = 'Loan Return Remaining Wizard'

    loan_request_id = fields.Many2one('hr.loan')
    amount = fields.Float("المبلغ المتبقي", readonly=True)
    payment_date = fields.Date('التاريخ', default=fields.Date.context_today, required=True)
    journal_id = fields.Many2one('account.journal', string='طريقة السداد', required=True,
                                 domain=['|', ('type', '=', 'bank'), ('type', '=', 'cash')])

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)

    # @api.depends('loan_request_id', 'loan_request_id.loan_lines')
    # def _compute_remaining_loan_amount(self):
    #     self.amount = sum([line.amount for line in self.loan_request_id.loan_lines if not line.paid])


    def action_return_remaining_loan(self):
        for rec in self:
            debit = credit = rec.currency_id.compute(rec.amount, rec.currency_id)

            move = {
                'name': '/',
                'journal_id': rec.journal_id.id,
                'ref': self.loan_request_id.name + '  استرجاع متبقي القرض ',
                'date': rec.payment_date,

                'line_ids': [(0, 0, {
                    'name': rec.loan_request_id.name + '/' + self.loan_request_id.employee_id.name + "   - استرجاع متبقي مبلغ القرض ",
                    'debit': debit,
                    'account_id': rec.journal_id.default_account_id.id,
                }), (0, 0, {
                    'name': rec.loan_request_id.name + '/' + self.loan_request_id.employee_id.name + "   - استرجاع متبقي مبلغ القرض ",
                    'credit': credit,
                    'account_id': rec.loan_request_id.emp_account_id.id,
                })]
            }
            move_id = self.env['account.move'].create(move)
            move_id.post()
            for line in rec.loan_request_id.loan_lines:
                line.paid = True
