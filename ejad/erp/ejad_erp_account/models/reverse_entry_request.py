# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReversEntryRequest(models.Model):
    _name = 'reverse.entry.request'
    _inherit = ['mail.thread']

    name = fields.Char('Sequence NUmber')
    original_move_id = fields.Many2one('account.move', string='Move')
    reversal_move_id = fields.Many2one('account.move', string='Reversal Move')
    reversal_date = fields.Date('Reversal Date')
    journal_id = fields.Many2one('account.journal', string='Journal')

    state = fields.Selection([
        ('draft', 'draft'),
        ('accounting', 'Accountant'),
        ('verfication', 'Financial Auditor'),
        ('account_department', 'Financial Manager'),
        ('finance_verfifcation', 'Financial Monitor'),
        ('manager', 'University Manager'),
        ('done', 'Done'),
        ('cancelled', 'Cancel'),
    ], string="State", default='draft', tracking=True, copy=False, )

    def action_submit(self):
        self.write({'state': 'accounting'})

    def action_accounting_approve(self):
        self.write({'state': 'verfication'})

    def action_verification(self):
        self.write({'state': 'account_department'})

    # def action_verification_approve(self):
    #     self.write({'state': 'account_department'})

    def action_department_approve(self):
        self.write({'state': 'finance_verfifcation'})

    def action_finance_verfifcation_approve(self):
        reversed_move = self.original_move_id._reverse_moves(self.reversal_date, self.journal_id or False)
        self.reversal_move_id = (self.env['account.move'].browse(reversed_move)).id
        self.write({'state': 'manager'})

    def action_manager_approve(self):
        self.write({'state': 'done'})

    def action_refuse(self):
        self.write({'state': 'cancelled'})

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('reverse.entry.request')
        result = super(ReversEntryRequest, self).create(vals)

        return result


# class AccountMoveReversal(models.TransientModel):
#     _inherit = 'account.move.reversal'
#
#     def reverse_moves(self):
#         ac_move_ids = self._context.get('active_ids', False)
#         for move in self.env['account.move'].browse(ac_move_ids):
#             reverse_request = self.env['reverse.entry.request'].create({
#                 'original_move_id': move.id,
#                 'reversal_date': self.date,
#                 'journal_id': self.journal_id.id or move.journal_id.id,
#             })
#             move.reverse_request_id = reverse_request.id
#
#         return {'type': 'ir.actions.act_window_close'}
