# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime


class AdministrativeCommunicationsOperationMove(models.Model):
    _name = "ac.operation.move"
    _description = "ac operation move"

    name = fields.Char(string='الاسم')
    date = fields.Datetime(string="تاريخ الحركة", default=fields.Datetime.now)
    operation_id = fields.Many2one('ac.operation', required=True, string='المعاملة')
    old_employee_id = fields.Many2one('hr.employee', string='الموظف القديم')
    new_employee_id = fields.Many2one('hr.employee', string='الموظف الجديد')
    src_dep_id = fields.Many2one('hr.department', string='الإدارة القديمة')
    dest_dep_id = fields.Many2one('hr.department', string='الإدارة الجديدة')
    user_id = fields.Many2one('res.users', string='الموظف المشرف', default=lambda self: self.env.user)
    notes = fields.Text('الملاحظات')

    src_name = fields.Char(string='من')
    dest_name = fields.Char(string='إلى')

    type = fields.Selection([
        ('create', 'إنشاء'),
        ('transfer', 'إحالة'),
        ('comment', 'تعليق'),
        ('export', 'تصدير'),
        ('read', 'قراءة'),
        ('save', 'حفظ'),
        ('update', 'تحديث'),
        ('cancel', 'إلغاء')
        ], string="النوع", required=True)
    type_transfer = fields.Selection([
        ('transfer_to_department', 'إحالة إلى إدارة'),
        ('transfer_to_employee', 'إحالة إلى موظف'),
        ('transfer_from_global_inbox', 'إحالة من الوارد العام'),
        ('transfer_to_global_outbox', 'إحالة إلى الصادر العام')], string='نوع الإحالة')
    transfer_guidance = fields.Many2one('ac.transfer.guidance', string='التوجيه')

    date_deadline = fields.Datetime(string="تاريخ الانجاز")

    @api.model
    def create(self, vals):
        vals.update({'name': self.env['ir.sequence'].next_by_code('ac.operation.move')})
        res = super(AdministrativeCommunicationsOperationMove, self).create(vals)
        return res
