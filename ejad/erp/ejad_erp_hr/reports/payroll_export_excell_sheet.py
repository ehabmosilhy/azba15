# -*- coding: utf-8 -*-

from odoo import models


class PayrolltoExcell(models.AbstractModel):
    _name = 'report.ejad_erp_hr.payroll_excel_xlsx'
    _description = 'Payroll Excel_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        payslip_batch_id = self.env['hr.payslip.run'].search([('id', '=', data['form']['payslip_batch_id'])],
                                                             limit=1)

        sheet = workbook.add_worksheet(payslip_batch_id.name)
        sheet.right_to_left()
        sheet.set_column(0, 3, 25)
        sheet.set_column(4, 15, 12)

        format1 = workbook.add_format(
            {'font_size': 13, 'align': 'center', 'valign': 'vcenter', 'right': True, 'left': True, 'bottom': True,
             'top': True,
             'bold': True})
        format2 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'right': True, 'left': True, 'bottom': True,
             'top': True,
             'bold': True})

        sheet.merge_range(0, 0, 1, 0, 'اسم الموظف (عربي)', format1)
        sheet.merge_range(0, 1, 1, 1, 'اسم الموظف (انجليزي)', format1)
        sheet.merge_range(0, 2, 1, 2, 'رقم الموظف', format1)
        sheet.merge_range(0, 3, 1, 3, 'رقم الهوية', format1)
        sheet.merge_range(0, 4, 1, 4, 'رقم الحساب البنكي', format1)
        sheet.merge_range(0, 5, 1, 5, 'اسم البنك ', format1)
        sheet.merge_range(0, 6, 1, 6, 'رمز قسيمة الدفع للموظف', format1)
        sheet.merge_range(0, 7, 1, 7, 'رقم دفع قسائم الدفع', format1)

        sheet.merge_range(0, 8, 1, 8, 'الراتب الصافي', format1)

        is_create_rule_header = False
        payslip_line_obj = self.env['hr.payslip.line']
        row = 2
        for slip in payslip_batch_id.slip_ids:
            if data['form']['employees_to_show'] != 'all':
                if slip.employee_id.payment_type != data['form']['employees_to_show']:
                    continue

            sheet.write(row, 0, slip.employee_id.name or '', format2)
            sheet.write(row, 1, slip.employee_id.en_name or '', format2)
            sheet.write(row, 2, slip.employee_id.emp_attendance_no or '', format2)
            sheet.write(row, 3, slip.employee_id.identification_id or '', format2)
            sheet.write(row, 4, slip.employee_id.bank_account_id.acc_number or '', format2)
            sheet.write(row, 5, slip.employee_id.bank_account_id.bank_id.name or '', format2)
            sheet.write(row, 6, slip.number or '', format2)
            net_salary_line = payslip_line_obj.search([('slip_id', '=', slip.id), ('is_net', '=', True)],
                                                      limit=1)
            exported_salary_rules = self.env['hr.salary.rule'].search([('is_export_excel', '=', True)])
            sheet.write(row, 7, payslip_batch_id.name or '', format2)

            sheet.write(row, 8, net_salary_line.total or 0, format2)

            col = 9
            for rule in exported_salary_rules:
                if not is_create_rule_header:
                    sheet.merge_range(0, col, 1, col, rule.name, format1)
                exported_payslip_line = payslip_line_obj.search(
                    [('slip_id', '=', slip.id), ('salary_rule_id', '=', rule.id)])
                sheet.write(row, col, exported_payslip_line.total or 0, format2)
                col += 1
            is_create_rule_header = True
            row += 1
