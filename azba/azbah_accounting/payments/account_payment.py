# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _prepare_payment_display_name(self):
        '''
        Hook method for inherit
        When you want to set a new name for payment, you can extend this method
        '''
        if not self.env.context.get('sanad'):
            return {
                'outbound-customer': _("Customer Reimbursement"),
                'inbound-customer': _("Customer Payment"),
                'outbound-supplier': _("Vendor Payment"),
                'inbound-supplier': _("Vendor Reimbursement"),
            }
        else:
            return {
                'outbound-customer': "",
                'inbound-customer': "",
                'outbound-supplier': "",
                'inbound-supplier': "",
            }

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        m = self.move_id
        default_account = self.journal_id
        print(m)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('sanad'):
            # get cash account id
            vals_list[0]['payment_method_line_id']=4
        payments = super().create(vals_list)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        if self.env.context.get('sanad'):
            # get cash account id
            cash_account_id = self.env['account.account'].search([('code', '=', '1201001')])
            if vals.get('line_ids'):
                for line in vals.get('line_ids'):
                    if line[2]['debit'] > 0:
                        line[2]['account_id'] = cash_account_id.id
                    else:
                        line[2]['account_id'] = self.journal_id.default_account_id.id
        res = super(AccountMove, self).write(vals)
        return res


'''    
    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        if self.env.context.get('sanad'):
            # get cash account id
            cash_account_id = self.env['account.account'].search([('code', '=', '1201001')])
            for payment in payments:
                for line in payment.move_id.line_ids:
                    line.unlink()

                if payment.payment_type == 'inbound':
                    payment.line_ids.create({'account_id': cash_account_id
                                                , 'partner_id': payment.partner_id
                                                , 'label': payment.partner_id
                                                , 'debit': payment.amount
                                             })

                    payment.line_ids.create({'account_id': payment.journal_id.default_account_id
                                                , 'partner_id': payment.partner_id
                                                , 'label': payment.partner_id
                                                , 'credit': payment.amount
                                             })

                else:
                    payment.line_ids.create({'account_id': cash_account_id
                                                , 'partner_id': payment.partner_id
                                                , 'label': payment.partner_id
                                                , 'credit': payment.amount
                                             })

                    payment.line_ids.create({'account_id': payment.journal_id.default_account_id
                                                , 'partner_id': payment.partner_id
                                                , 'label': payment.partner_id
                                                , 'debit': payment.amount
                                             })
        return payments
'''
