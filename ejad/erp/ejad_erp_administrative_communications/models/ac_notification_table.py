# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class ACNotificationTable(models.Model):
    _name = "ac.notification.table"
    _description = "ac notification table"

    operation_id = fields.Many2one('ac.operation', string='المعاملة')
    notification_date = fields.Datetime('تاريخ ووقت التنبيه')
    to_notify_manager = fields.Boolean('To Notify Managers?')
