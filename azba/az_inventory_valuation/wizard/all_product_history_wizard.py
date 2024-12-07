from odoo import models, fields, api
import io
import xlsxwriter
import base64
from datetime import datetime, timedelta
from collections import defaultdict


class AllProductHistoryWizard(models.TransientModel):
    _name = 'all_product.history.wizard'
    _description = 'All Product History Wizard'

    start_date = fields.Datetime(string='Start Date', required=True)
    end_date = fields.Datetime(string='End Date', required=True)
    report_file = fields.Binary(string='Report File')
    report_filename = fields.Char(string='Report Filename', default='product_balance.xlsx')

    

    def get_product_balance(self, date):
        self.ensure_one()

        if date.time() == datetime.min.time():
            date = date - timedelta(days=1)
            date = date.replace(hour=23, minute=59, second=59, microsecond=0)

        domain = [('create_date', '<=', date), ('product_id.type', '=', 'product')]
        stock_valuation_lines = self.env['stock.valuation.layer'].search(domain)
        
        product_quantities = defaultdict(float)
        for line in stock_valuation_lines:
            product_quantities[line.product_id.id] += line.quantity

        balance_data = []
        for product_id, total_quantity in product_quantities.items():
            product = self.env['product.product'].browse(product_id)
            if product:
                code = f'{product.product_tmpl_id.code.strip()}' if product.product_tmpl_id.code else '[]'
                balance_data.append({
                    'product_id': product_id,
                    'product_code': code,
                    'product_name': product.name,
                    'quantity': total_quantity,
                })

        return balance_data

    def action_generate_report(self):
        initial_balances = self.get_product_balance(self.start_date)
        final_balances = self.get_product_balance(self.end_date)

        # Combine data for report
        report_data = []
        products_seen = set()

        # Process initial balances
        for balance in initial_balances:
            products_seen.add(balance['product_id'])
            report_data.append({
                'product_code': balance['product_code'],
                'product_name': balance['product_name'],
                'initial_balance': balance['quantity'],
                'final_balance': 0.0,
            })

        # Process final balances
        for balance in final_balances:
            if balance['product_id'] in products_seen:
                # Update existing entry
                for entry in report_data:
                    if entry['product_code'] == balance['product_code']:
                        entry['final_balance'] = balance['quantity']
                        break
            else:
                # Add new entry
                report_data.append({
                    'product_code': balance['product_code'],
                    'product_name': balance['product_name'],
                    'initial_balance': 0.0,
                    'final_balance': balance['quantity'],
                })

        self._generate_excel_report(report_data)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Balance Report',
            'view_mode': 'form',
            'res_model': 'all_product.history.wizard',
            'res_id': self.id,
            'target': 'new',
        }

    def _generate_excel_report(self, report_data):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Product Balance Report')

        # Define headers
        headers = ['Product Code', 'Product Name', 'Initial Balance', 'Final Balance']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Write data
        for row_num, line in enumerate(report_data, start=1):
            worksheet.write(row_num, 0, line['product_code'])
            worksheet.write(row_num, 1, line['product_name'])
            worksheet.write(row_num, 2, line['initial_balance'])
            worksheet.write(row_num, 3, line['final_balance'])

        workbook.close()
        output.seek(0)
        self.report_file = base64.b64encode(output.read())

    def download_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=all_product.history.wizard&id={}&field=report_file&filename_field=report_filename&download=true'.format(
                self.id),
            'target': 'new',
        }
