# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    name = fields.Char('Order Reference', required=True, index=True, copy=False, default='جديد')
    original_file = fields.Binary(string="ملف العرض الاصلي", states={'purchase': [('required', True)]})
    file_name = fields.Char(string="File Name")
    origin = fields.Char(readonly=True)
    requisition_id = fields.Many2one(readonly=True)

    
    def button_approve(self, force=False):
        if self.file_name:
            super(PurchaseOrder, self).button_approve(force=force)
        else:
            raise ValidationError('يجب ارفاق ملف العرض الاصلي .!')
