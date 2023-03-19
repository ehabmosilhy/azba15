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



    @api.depends('available_payment_method_line_ids')
    def _compute_payment_method_line_id(self):
        ''' Compute the 'payment_method_line_id' field.
        This field is not computed in '_compute_payment_method_line_fields' because it's a stored editable one.
        '''

        for pay in self:

            #  /\_/\
            # ( o.o )
            #  > ^ <
            # Beginning: Ehab
            # The payment method gets recalculated after the creation of the payment
            if self.env.context.get('sanad'):
                pay.payment_method_line_id = 2 if self.env.context.get('default_payment_type')=='outbound' else 1

            #  (\_/)
            #  (^.^)
            #   \_/
            # Ending of the code

            else:
                available_payment_method_lines = pay.available_payment_method_line_ids
        
                # Select the first available one by default.
                if pay.payment_method_line_id in available_payment_method_lines:
                    pay.payment_method_line_id = pay.payment_method_line_id
                elif available_payment_method_lines:
                    pay.payment_method_line_id = available_payment_method_lines[0]._origin
                else:
                    pay.payment_method_line_id = False

@api.model_create_multi
def create(self, vals_list):
    if self.env.context.get('sanad'):
        vals_list[0]['payment_method_line_id'] = 2
    payments = super().create(vals_list)

    return payments


class AccountMove(models.Model):
    _inherit = 'account.move'

    def write(self, vals):
        if self.env.context.get('sanad'):
            #  /\_/\
            # ( o.o )
            #  > ^ <
            # The two parties of the move will be : 1- Cash and 2- Whatever account bound to the journal
            # The other account of the move must fulfill these conditions:
            #  1- Internal Type: "receivable" or "payable"
            #  2- Not a liquidity account
            #  3- Bound to the journal (sanad_account_id)

            cash_account_id = self.env['account.account'].search([('code', '=', '1201001')])
            sanad_account_id = self.journal_id.sanad_account_id
            if vals.get('line_ids'):
                for line in vals.get('line_ids'):
                    if self.env.context.get('default_payment_type') == 'outbound':
                        if line[2]['credit'] >0:
                            line[2]['account_id'] = cash_account_id.id
                        else:
                            line[2]['account_id'] = sanad_account_id.id
                    else:
                        if line[2]['debit'] >0:
                            line[2]['account_id'] = cash_account_id.id
                        else:
                            line[2]['account_id'] = sanad_account_id.id

        res = super(AccountMove, self).write(vals)
        return res
