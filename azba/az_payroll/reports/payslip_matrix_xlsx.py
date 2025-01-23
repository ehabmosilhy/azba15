from odoo import models
from collections import OrderedDict


class PayslipMatrixXlsxReport(models.AbstractModel):
    _name = 'report.az_payroll.report_payslip_matrix_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Payslip Matrix Excel Report'

    def _get_salary_rules(self, payslips):
        """Get all unique salary rules from payslips."""
        rules = OrderedDict()
        for payslip in payslips:
            for line in payslip.line_ids:
                if line.salary_rule_id.name not in rules:
                    rules[line.salary_rule_id.name] = {
                        'name': line.salary_rule_id.name,
                        'sequence': line.salary_rule_id.sequence,
                        'category': line.category_id.name or '',
                    }
        # Sort rules by sequence
        return OrderedDict(sorted(rules.items(), key=lambda x: (x[1]['sequence'], x[1]['name'])))

    def generate_xlsx_report(self, workbook, data, payslips):
        if not payslips:
            return

        sheet = workbook.add_worksheet('Payslips Summary')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True, 
            'align': 'center',
            'bg_color': '#2F75B5',
            'font_color': 'white',
            'border': 1,
            'border_color': '#1F4E78'
        })
        
        data_format = workbook.add_format({
            'align': 'left',
            'border': 1,
            'border_color': '#E0E0E0'
        })
        
        number_cell_format = workbook.add_format({
            'align': 'center',
            'border': 1,
            'border_color': '#E0E0E0'
        })
        
        date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'align': 'center',
            'border': 1,
            'border_color': '#E0E0E0'
        })
        
        amount_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
            'border': 1,
            'border_color': '#E0E0E0'
        })

        total_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0.00',
            'align': 'right',
            'border': 1,
            'bg_color': '#F2F2F2',
            'border_color': '#E0E0E0'
        })

        # Get all unique salary rules
        salary_rules = self._get_salary_rules(payslips)
        
        # Fixed columns
        columns = OrderedDict([
            ('employee', {'name': 'Employee', 'width': 30}),
            ('number', {'name': 'Number', 'width': 15}),
            ('date_from', {'name': 'Start Date', 'width': 12}),
            ('date_to', {'name': 'End Date', 'width': 12}),
        ])
        
        # Add salary rule columns
        for rule_name, rule_info in salary_rules.items():
            columns[rule_name] = {
                'name': f"{rule_info['name']} ({rule_info['category']})",
                'width': 15,
                'category': rule_info['category']
            }

        # Set column widths
        for col, (_, col_info) in enumerate(columns.items()):
            sheet.set_column(col, col, col_info['width'])

        # Write headers
        for col, (_, col_info) in enumerate(columns.items()):
            sheet.write(0, col, col_info['name'], header_format)

        # Write data
        row = 1
        for payslip in payslips:
            col = 0
            # Write fixed columns
            sheet.write(row, col, payslip.employee_id.name, data_format)
            col += 1
            sheet.write(row, col, payslip.number or '', number_cell_format)
            col += 1
            sheet.write(row, col, payslip.date_from, date_format)
            col += 1
            sheet.write(row, col, payslip.date_to, date_format)
            col += 1

            # Create dict of line values for quick lookup
            line_values = {line.salary_rule_id.name: line.total for line in payslip.line_ids}
            
            # Write rule values
            for rule_name, rule_info in salary_rules.items():
                value = line_values.get(rule_name, 0.0)
                # Make deductions negative
                if rule_info['category'].lower().find('deduction') >= 0:
                    value = -abs(value)
                sheet.write(row, col, value, amount_format)
                col += 1
            
            row += 1

        # Write totals
        if row > 1:
            sheet.write(row, 0, 'Totals', header_format)
            sheet.write(row, 1, '', header_format)
            sheet.write(row, 2, '', header_format)
            sheet.write(row, 3, '', header_format)
            
            # Add sum formulas for each rule column
            for col in range(4, len(columns)):
                col_letter = chr(65 + col)
                formula = f'=SUM({col_letter}2:{col_letter}{row})'
                sheet.write_formula(row, col, formula, total_format)
