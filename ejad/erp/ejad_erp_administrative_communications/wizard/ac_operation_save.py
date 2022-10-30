# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class ACOperationTransfer(models.TransientModel):
    _name = 'wiz.ac.operation.save'
    _description = 'wiz ac operation save'

    place_id = fields.Many2one(comodel_name="ac.place.save.operation", string="مكان الحفظ", required=True)
    notes = fields.Text('التعليق')

    
    def action_save_operation(self):
        operation_id = self.env['ac.operation'].browse(self.env.context.get('active_ids'))

        move_data = {'type': 'save',
                     'date': datetime.today(),
                     'operation_id': operation_id.id,
                     'user_id': self.env.user.id,
                     'notes': self.notes}
        self.env['ac.operation.move'].create(move_data)

        msg = "تم حفظ المعاملة"

        operation_id.write({'message': msg})
        operation_id.write({'state': 'done'})
        operation_id.write({'is_saved': True})
        operation_id.write({'place_id': self.place_id.id})

        #action = self.env.ref('ejad_erp_administrative_communications.action_ac_operation_in_general').read()[0]
        return True

