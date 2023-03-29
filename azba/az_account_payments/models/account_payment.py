# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        super(AccountPayment, self)._onchange_journal()
        self.is_internal_transfer = True

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('sanad') and self.env.context.get('default_is_internal_transfer'):
            payments = super().create(vals_list)
        return payments
