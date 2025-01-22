from odoo import models


class PayslipXlsxReport(models.AbstractModel):
    _name = 'report.az_payroll.report_payslip_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Payslip Excel Report'

    def generate_xlsx_report(self, workbook, data, payslips):
        for payslip in payslips:
            # Sheet name - max 31 chars
            sheet_name = (payslip.employee_id.name or 'Payslip')[:31]
            sheet = workbook.add_worksheet(sheet_name)
            
            # Formats
            header_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D3D3D3'})
            title_format = workbook.add_format({'bold': True, 'align': 'left'})
            date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
            number_format = workbook.add_format({'num_format': '#,##0.00'})

            # Column widths
            sheet.set_column('A:A', 15)  # Code
            sheet.set_column('B:B', 40)  # Name
            sheet.set_column('C:E', 15)  # Quantity, Rate, Total

            # Headers
            row = 0
            sheet.write(row, 0, 'Employee:', title_format)
            sheet.write(row, 1, payslip.employee_id.name)
            
            row += 1
            sheet.write(row, 0, 'Period:', title_format)
            sheet.write(row, 1, f'{payslip.date_from} - {payslip.date_to}')
            
            row += 2
            headers = ['Code', 'Description', 'Quantity', 'Rate', 'Total']
            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_format)

            # Data
            row += 1
            for line in payslip.line_ids:
                sheet.write(row, 0, line.code)
                sheet.write(row, 1, line.name)
                sheet.write(row, 2, line.quantity, number_format)
                sheet.write(row, 3, line.rate, number_format)
                sheet.write(row, 4, line.total, number_format)
                row += 1

            # Total
            row += 1
            sheet.write(row, 0, 'Total', title_format)
            total_formula = f'=SUM(E{row-len(payslip.line_ids)}:E{row})'
            sheet.write_formula(row, 4, total_formula, number_format)
