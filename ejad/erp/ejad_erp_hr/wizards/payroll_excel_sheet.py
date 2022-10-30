# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PayrollExcel(models.TransientModel):
    _name = "payroll.excel.sheet.wizard"
    _description = "Export Payroll Excel Sheet"

    payslip_batch_id = fields.Many2one('hr.payslip.run', string='Payslip Batch')
    employees_to_show = fields.Selection(
        [('all', 'كل الموظفين'), ('bank', 'كل الموظفين على البنك فقط'), ('cash', 'كل الموظفين على الصندوق فقط')],

        string="إظهار الموظفين بالملف", default='all')

    
    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'hr.payslip.run'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]

        return self.env.ref('ejad_erp_hr.payroll_excel_sheet').report_action(self, data=datas)
