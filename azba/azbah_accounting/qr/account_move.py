# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_repr


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        if 'invoice_date' in vals:
            vals['l10n_sa_confirmation_datetime']=vals['invoice_date']
            # super(AccountMove, self)._compute_qr_code_str()
        res = super(AccountMove, self).write(vals)
        return res

    def _post(self, soft=True):
        res = super()._post(soft)
        for record in self:
            if record.country_code == 'SA' and record.move_type in ('out_invoice', 'out_refund'):
                if not record.l10n_sa_show_delivery_date:
                    raise UserError(_('Delivery Date cannot be empty'))
                self.write({
                    'l10n_sa_confirmation_datetime': self.invoice_date
                })
        return res
