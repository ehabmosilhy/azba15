# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class ACUsersViewer(models.Model):
    _name = "ac_users.viewer"
    _description = "ac users viewer"

    user = fields.Many2one('res.users', string='المستخدم')
    seen_date_time = fields.Datetime('وقت الإطلاع على المعاملة')

    operation_id = fields.Many2one('ac.operation', string='المعاملة')
