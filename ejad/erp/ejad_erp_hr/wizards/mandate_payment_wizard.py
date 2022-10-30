# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MandatePayment(models.TransientModel):
    _name = 'mandate.payment.wizard'
    _description = 'Mandate Payment Wizard'

    mandate_request_id = fields.Many2one('hr.mandate.request')
    payment_date = fields.Date('Payment Date',default=fields.Date.context_today,required=True)
    journal_id = fields.Many2one('account.journal', string='Journal',required=True,
                                 domain=['|', ('type', '=', 'bank'), ('type', '=', 'cash')])


    def action_validate_mandate_payment(self):
        # if not self.journal_id.default_account_id:
        #     raise UserError(_(
        #         "Please fill default credit account fields in the selected journal in order to create journal entery"))
        #
        # if not self.mandate_request_id.type_id.account_id:
        #     raise UserError(
        #         _("Please fill account fields in the selected mandate type in order to create journal entery"))
        #
        # move_id = self.env['account.move'].create({
        #     'journal_id': self.journal_id.id,
        #     'ref': self.mandate_request_id.name + ' انتداب  ',
        #     'date': self.payment_date
        # })
        # aml = self.env['account.move.line'].with_context(check_move_validity=False)
        # aml.create({
        #     'name': self.mandate_request_id.employee_id.name + "   - بدل انتداب ",
        #     'account_id': self.mandate_request_id.type_id.account_id.id,
        #     'credit': 0,
        #     'debit': self.mandate_request_id.total_mandate_amount,
        #     'move_id': move_id.id
        #
        # })
        # aml.create({
        #     'name': self.mandate_request_id.employee_id.name + "  - بدل انتداب ",
        #     'account_id': self.journal_id.default_account_id.id,
        #     'credit': self.mandate_request_id.total_mandate_amount,
        #     'debit': 0,
        #     'move_id': move_id.id
        #
        # })
        # move_id.post()
        self.mandate_request_id.state = 'mandat_amount_paid'
        # self.mandate_request_id.move_id = move_id
        # self.mandate_request_id.journal_id = self.journal_id
        return {'type': 'ir.actions.act_window_close'}
