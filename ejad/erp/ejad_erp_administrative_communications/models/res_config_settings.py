# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_ac_archive_days = fields.Integer(default_model='res.company',  default=28,
                                             string='عدد الأيام للأرشفة')
    default_host = fields.Char(default_model='res.company')
    default_operation_notification = fields.Integer(default_model='res.company',
                                                    string='نسبة الاشعار على المعاملة %')
    checking_date = fields.Datetime(default_model='res.company', string="Checking")


class ResCompany(models.Model):
    _inherit = 'res.company'

    ac_archive_days = fields.Integer(string='عدد الأيام للأرشفة')
    host = fields.Char(string="Host")
    operation_notification = fields.Integer(string="نسبة الاشعار على المعاملة %", default=20)
    checking_date = fields.Datetime(string="Checking")
