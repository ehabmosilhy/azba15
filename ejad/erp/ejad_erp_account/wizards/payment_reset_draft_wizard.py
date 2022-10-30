# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ResetDraft(models.TransientModel):
    _name = 'payment.reset.wizard'

    comment = fields.Text('Comments', required=True)

    def action_validate_payment_reset(self):

        payment_id = self.env['account.payment'].browse(self._context.get('active_id', False))
        for move in payment_id.move_line_ids.mapped('move_id'):
            if payment_id.invoice_ids:
                move.line_ids.remove_move_reconcile()
            move.button_cancel()
            move.unlink()
        payment_id.state = 'draft'
        payment_id.message_post(body=self.comment, message_type='comment')
        return {'type': 'ir.actions.act_window_close'}
