# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchaseRequisitionRefuse(models.TransientModel):
    _name = 'purchase.requisition.refuse'
    _description = 'Get Refuse Reason'

    refuse_reason_id = fields.Many2one('requisition.refuse.reason', required=True, string='سبب الرفض')
    refuse_reason = fields.Text('ملاحظات الرفض', required=True)

    def action_refuse_reason_apply(self):
        requisition_request = self.env['purchase.requisition.request'].browse(self.env.context.get('active_ids'))
        requisition_request.write({'state': 'refused',
                                   'refuse_reason_id': self.refuse_reason_id.id,
                                   'refuse_state':requisition_request.state,
                                   'refuse_message':self.refuse_reason,
                                   'refuse_user_id':self.env.context.get('uid')})
