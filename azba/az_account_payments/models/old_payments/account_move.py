# -*- coding: utf-8 -*-
from lxml import etree

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountBill(models.Model):
    _inherit = "account.move"

    batch_id = fields.Many2one('account.batch.vendor.bill')



