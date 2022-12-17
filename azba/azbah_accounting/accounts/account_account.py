# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountAccount(models.Model):
    _inherit = "account.account"
    parent_id = fields.Many2one('account.account', string='Parent Account')

    def update_parents(self):
        accounts = self.env['account.account'].search([]).sorted(key=lambda x: len(x.code), reverse=True).sudo()
        for ac in accounts:
            for p in accounts:
                if ac.code.startswith(p.code) and int(p.code) < int(ac.code):
                    ac.parent_id = p.id
                    break
