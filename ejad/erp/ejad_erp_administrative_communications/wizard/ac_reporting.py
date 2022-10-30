# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError


class ACReporting(models.TransientModel):
    _name = 'wiz.ac.report'
    _description = 'wiz ac report'

    report_type = fields.Selection([
        ('global_inbox', 'تقرير معاملات الوارد العام'),
        ('global_outbox', 'تقرير معاملات الصادر العام'),
        ('internal', 'تقرير المعاملات الداخلية'),
        ('saved', 'تقرير المعاملات المحفوظة'),
        ('late', 'تقرير المعاملات المتأخرة'),
        ('transfer', 'تقرير قائمة الإحالات'),
        ('all', 'تقرير إجمالي المعاملات')], string="نوع التقرير", required=True)

    external_partner_ids = fields.Many2many(comodel_name="res.partner", string="الجهة المعنية")
    department_id = fields.Many2one('hr.department', string="الادارة",)
    assigned_employee_id = fields.Many2one('hr.employee', string='الموظف')
    advanced = fields.Boolean(string="بحث متقدم")

    date_from = fields.Datetime(string='تاريخ البدء', required=True)
    date_to = fields.Datetime(string='تاريخ الانتهاء', required=True, default=fields.Datetime.now)

    @api.onchange('date_from', 'date_to')
    def _onchange_type_op(self):
        if self.date_from and self.date_to:
            date_from = str(self.date_from)
            date_to = str(self.date_to)
            first = datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S')
            last = datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S')
            if last < first:
                raise UserError(_("التاريخ الأول يجب أن يكون أصغر من التاريخ الثاني .."))


    
    def check_report(self):

        data = dict()
        data['form'] = self.read(['department_id', 'date_from', 'date_to',
                                  'report_type', 'external_partner_ids', 'assigned_employee_id'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        return self.env.ref('ejad_erp_administrative_communications.action_admin_com_reporting').report_action(self, data=data)
