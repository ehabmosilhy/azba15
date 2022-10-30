# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class EndOfServices(models.TransientModel):
    _name = 'hr.end.service.wizard'
    _description = 'Hr End Service Wizard'

    end_request_id = fields.Many2one('hr.end.service')
    name = fields.Char('حساب نهايه الخدمة')
    amount = fields.Float("amount", related='end_request_id.benefits', readonly=True)
    payment_date = fields.Date('Payment Date', default=fields.Date.context_today, required=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
                                 domain=['|', ('type', '=', 'bank'), ('type', '=', 'cash')])

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)


    def action_validate_endofservice_amount(self):
        for rec in self:
            # debit = credit = rec.currency_id.compute(rec.amount, rec.currency_id)
            #
            # move = {
            #     'name': '/',
            #     'journal_id': rec.journal_id.id,
            #     'ref': self.end_request_id.name + ' مكافئة  ',
            #     'date': rec.payment_date,
            #
            #     'line_ids': [(0, 0, {
            #         'name': rec.end_request_id.name or '/' + self.end_request_id.employee_id.name + "   - مكافئة نهاية الخدمة ",
            #         'debit': debit,
            #         'account_id': rec.end_request_id.company_id.benefit_account_id.id,
            #         'partner_id': rec.end_request_id.employee_id.user_id.partner_id.id,
            #     }), (0, 0, {
            #         'name': rec.end_request_id.name or '/' + self.end_request_id.employee_id.name + "   - مكافئة نهاية الخدمة ",
            #         'credit': credit,
            #         'account_id': rec.journal_id.default_account_id.id,
            #         'partner_id': rec.end_request_id.employee_id.user_id.partner_id.id,
            #     })]
            # }
            # move_id = self.env['account.move'].create(move)
            # move_id.post()
            # self.end_request_id.state = 'benefits_paid'
            # self.end_request_id.journal_id = self.journal_id
            # self.end_request_id.move_id = move_id
            self.end_request_id.state = 'benefits_paid'
            return True
