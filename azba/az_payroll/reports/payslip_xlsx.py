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
            header_format = workbook.add_format({
                'bold': True, 
                'align': 'center',
                'bg_color': '#2F75B5',  # Professional blue
                'font_color': 'white',
                'border': 1,
                'border_color': '#1F4E78'  # Darker blue for border
            })
            
            title_format = workbook.add_format({
                'bold': True,
                'align': 'left',
                'font_size': 12,
                'font_color': '#2F75B5'
            })
            
            data_format = workbook.add_format({
                'align': 'left',
                'border': 1,
                'border_color': '#E0E0E0'  # Light gray border
            })
            
            number_format = workbook.add_format({
                'num_format': '#,##0.00',
                'align': 'right',
                'border': 1,
                'border_color': '#E0E0E0'
            })
            
            last_row_format = workbook.add_format({
                'bold': True,
                'align': 'left',
                'bg_color': '#F2F2F2',  # Light gray background
                'border': 1,
                'border_color': '#E0E0E0'
            })
            
            last_row_number_format = workbook.add_format({
                'bold': True,
                'num_format': '#,##0.00',
                'align': 'right',
                'bg_color': '#F2F2F2',
                'border': 1,
                'border_color': '#E0E0E0'
            })

            category_format = workbook.add_format({
                'align': 'left',
                'border': 1,
                'border_color': '#E0E0E0',
                'italic': True,
                'font_color': '#666666'  # Gray color for category
            })

            # Column widths
            sheet.set_column('A:A', 15)  # Category
            sheet.set_column('B:B', 45)  # Description
            sheet.set_column('C:C', 20)  # Total

            # Headers
            row = 0
            sheet.write(row, 0, 'Employee:', title_format)
            sheet.merge_range(row, 1, row, 2, payslip.employee_id.name, workbook.add_format({'font_size': 12}))
            
            row += 1
            sheet.write(row, 0, 'Period:', title_format)
            sheet.merge_range(row, 1, row, 2, f'{payslip.date_from} - {payslip.date_to}', workbook.add_format({'font_size': 12}))
            
            row += 2
            headers = ['Category', 'Description', 'Amount']
            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_format)

            # Data
            row += 1
            lines = payslip.line_ids
            for i, line in enumerate(lines):
                is_last_row = i == len(lines) - 1
                row_format = last_row_format if is_last_row else data_format
                number_row_format = last_row_number_format if is_last_row else number_format
                
                # Get category name
                category = line.category_id.name or ''
                
                # Determine if it's a deduction (negative amount)
                amount = line.total
                if category.lower().find('deduction') >= 0:
                    amount = -abs(amount)  # Make sure it's negative
                
                sheet.write(row, 0, category, category_format if not is_last_row else last_row_format)
                sheet.write(row, 1, line.name, row_format)
                sheet.write(row, 2, amount, number_row_format)
                row += 1
