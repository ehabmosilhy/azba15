# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ReversEntry(models.TransientModel):
    _name = 'reverse.entry.wizard'

    date = fields.Date(string='Reversal date', default=fields.Date.context_today, required=True)
    journal_id = fields.Many2one('account.journal', string='Journal')
    reason = fields.Text('Reason', required=True)

    def action_validate_reserve_entry(self):
        payment_id = self.env['account.payment'].browse(self._context.get('active_id', False))

        for move in payment_id.move_line_ids.mapped('move_id'):
            reversed_move = move.reverse_moves(self.date, self.journal_id or False)
            payment_id.reversed_move = (self.env['account.move'].browse(reversed_move)).name

        payment_id.state = 'cancelled'
        payment_id.cancel_reasons = self.reason
        return {'type': 'ir.actions.act_window_close'}
