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
        if not self._context.get('sanad'):
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
