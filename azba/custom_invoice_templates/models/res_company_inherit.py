# -*- coding: utf-8 -*-
###############################################################################
#
#    ATIT.
#    Copyright (C) 2020-TODAY ATIT.
#
###############################################################################
from odoo import models, api, fields, _


class Company(models.Model):
    _inherit = 'res.company'
    iso_number = fields.Char(default='ISO 22000:2005')