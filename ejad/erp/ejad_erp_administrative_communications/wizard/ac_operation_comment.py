# -*- coding: utf-8 -*-

from odoo import api, fields, models
from datetime import datetime


class ACOperationComment(models.TransientModel):
    _name = 'wiz.ac.operation.comment'
    _description = 'wiz ac operation comment'

    date = fields.Datetime(string="التاريخ", default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='الموظف المشرف', default=lambda self: self.env.user)
    comment = fields.Text('التعليق')

    
    def action_add_comment(self):
        operation_id = self.env['ac.operation'].browse(self.env.context.get('active_ids'))
        self.env['ac.operation.comment'].create({'operation_id': operation_id.id, 'comment': self.comment})

        move_data = {'type': 'comment',
                     'operation_id': operation_id.id,
                     'user_id': self.env.user.id,
                     'notes': self.comment,
                     }
        self.env['ac.operation.move'].create(move_data)
