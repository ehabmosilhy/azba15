from odoo import models, fields, api
import io
import xlsxwriter
import base64
from datetime import datetime

class ProductHistoryWizard(models.TransientModel):
    _name = 'product.history.wizard'
    _description = 'Product History Wizard'

    start_date = fields.Datetime(string='Start Date', required=True)
    end_date = fields.Datetime(string='End Date', required=True)
    report_file = fields.Binary(string='Report File')
    report_filename = fields.Char(string='Report Filename', default='product_history.xlsx')

    def _get_stock_moves(self, product, date_start=None, date_end=None):
        domain = [
            ('state', '=', 'done'),
        ]
        if date_start:
            domain.append(('date', '>=', date_start))
        if date_end:
            domain.append(('date', '<=', date_end))
        return self.env['stock.move'].search(domain)

    def get_product_history(self):
        self.ensure_one()
        
        # Get products based on selection
        products = self.env['product.product'].search([('type', '=', 'product')])
        
        history_lines = []
        StockMove = self.env['stock.move']
        
        for product in products:
            # Get initial balance
            initial_moves = self._get_stock_moves(product, date_end=self.start_date)
            initial_qty = 0
            for move in initial_moves:
                if move.location_dest_id.usage == 'internal':
                    initial_qty += move.product_qty
                if move.location_id.usage == 'internal':
                    initial_qty -= move.product_qty
            
            # Get moves within period
            period_moves = self._get_stock_moves(product, self.start_date, self.end_date)
            
            # Calculate ins and outs
            total_in = sum(move.product_qty 
                         for move in period_moves 
                         if move.location_dest_id.usage == 'internal' 
                         and move.location_id.usage != 'internal')
            
            total_out = sum(move.product_qty 
                          for move in period_moves 
                          if move.location_id.usage == 'internal' 
                          and move.location_dest_id.usage != 'internal')
            
            # Calculate final balance
            final_balance = initial_qty + total_in - total_out
            
            # Only include products with activity or balance
            if initial_qty != 0 or final_balance != 0 or total_in != 0 or total_out != 0:
                code = product.default_code or ''
                history_lines.append({
                    'product_code': code,
                    'product_name': product.name,
                    'initial_balance': initial_qty,
                    'total_in': total_in,
                    'total_out': total_out,
                    'final_balance': final_balance,
                })

        self._generate_excel_report(history_lines)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Product History',
            'view_mode': 'form',
            'res_model': 'product.history.wizard',
            'res_id': self.id,
            'target': 'new',
        }

    def _generate_excel_report(self, history_lines):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Product History')

        # Add headers
        headers = ['Product Code', 'Product Name', 'Initial Balance', 'Total In', 'Total Out', 'Final Balance']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Add data
        for row_num, line in enumerate(history_lines, start=1):
            worksheet.write(row_num, 0, line['product_code'])
            worksheet.write(row_num, 1, line['product_name'])
            worksheet.write(row_num, 2, line['initial_balance'])
            worksheet.write(row_num, 3, line['total_in'])
            worksheet.write(row_num, 4, line['total_out'])
            worksheet.write(row_num, 5, line['final_balance'])

        workbook.close()
        output.seek(0)
        self.report_file = base64.b64encode(output.read())
        self.report_filename = f'product_history_{fields.Date.today()}.xlsx'

    def download_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': f'web/content/?model=product.history.wizard&id={self.id}&field=report_file&filename_field=report_filename&download=true',
            'target': 'new',
        }
