from odoo import models, fields, api
import io
import xlsxwriter
import base64
from datetime import datetime, timedelta

class ProductBalanceWizard(models.TransientModel):
    _name = 'product.balance.wizard'
    _description = 'Product Balance Wizard'

    start_date = fields.Datetime(string='Start Date', required=True)
    end_date = fields.Datetime(string='End Date', required=True)
    report_file = fields.Binary(string='Report File')
    report_filename = fields.Char(string='Report Filename', default='product_balance.xlsx')

    def _get_quantity_at_date(self, product, date):
        if date.time() == datetime.min.time():
            date = date - timedelta(days=1)
            date = date.replace(hour=23, minute=59, second=59, microsecond=0)

        domain = [
            ('create_date', '<=', date),
            ('product_id', '=', product.id),
            ('product_id.type', '=', 'product')
        ]
        stock_valuation_lines = self.env['stock.valuation.layer'].search(domain)
        return sum(line.quantity for line in stock_valuation_lines)

    def _get_stock_moves(self, product, date_start=None, date_end=None):
        domain = [
            ('state', '=', 'done'),
            ('product_id', '=', product.id),
            '|',
                ('picking_id', '=', False),  # Include adjustment moves
                ('picking_id.picking_type_id.code', 'in', ['incoming', 'outgoing', 'mrp_operation']),
        ]
        if date_start:
            domain.append(('date', '>=', date_start))
        if date_end:
            domain.append(('date', '<=', date_end))
        return self.env['stock.move'].search(domain, order='date asc')  # Order by date for proper adjustment processing

    def get_product_balance(self):
        self.ensure_one()
        
        # Get products with stock moves
        products = self.env['product.product'].search([('type', '=', 'product')])
        
        balance_lines = []
        
        for product in products:
            # Get initial balance using stock valuation layers
            initial_qty = self._get_quantity_at_date(product, self.start_date)
            
            # Get moves within period
            period_moves = self._get_stock_moves(product, self.start_date, self.end_date)
            
            total_in = 0
            total_out = 0
            running_total = initial_qty
            
            for move in period_moves:
                if move.picking_id:
                    # Regular moves
                    if move.picking_id.picking_type_id.code == 'incoming':
                        total_in += move.product_qty
                        running_total += move.product_qty
                    elif move.picking_id.picking_type_id.code in ['outgoing', 'mrp_operation']:
                        total_out += move.product_qty
                        running_total -= move.product_qty
                else:
                    # Adjustment moves
                    adjustment_qty = move.product_qty
                    difference = adjustment_qty - running_total
                    
                    if difference > 0:
                        total_in += difference
                    else:
                        total_out += abs(difference)
                    
                    running_total = adjustment_qty
            
            # Get final balance using stock valuation layers
            final_qty = self._get_quantity_at_date(product, self.end_date)
            
            # Only include products with activity or balance
            if initial_qty != 0 or final_qty != 0 or total_in != 0 or total_out != 0:
                code = f'{product.product_tmpl_id.code.strip()}' if product.product_tmpl_id.code else '[]'
                balance_lines.append({
                    'product_code': code,
                    'initial_balance': initial_qty,
                    'product_name': product.name,
                    'total_in': total_in,
                    'total_out': total_out,
                    'final_balance': final_qty,
                })

        # Sort balance_lines by product_code
        balance_lines = sorted(balance_lines, key=lambda x: x['product_code'] or '')

        self._generate_excel_report(balance_lines)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Balance',
            'view_mode': 'form',
            'res_model': 'product.balance.wizard',
            'res_id': self.id,
            'target': 'new',
        }

    def _generate_excel_report(self, balance_lines):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Product Balance')

        # Add headers
        headers = ['Product Code', 'Product Name', 'Initial Balance', 'Total In', 'Total Out', 'Final Balance']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Add data
        for row_num, line in enumerate(balance_lines, start=1):
            worksheet.write(row_num, 0, line['product_code'])
            worksheet.write(row_num, 1, line['product_name'])
            worksheet.write(row_num, 2, line['initial_balance'])
            worksheet.write(row_num, 3, line['total_in'])
            worksheet.write(row_num, 4, line['total_out'])
            worksheet.write(row_num, 5, line['final_balance'])

        workbook.close()
        self.write({
            'report_file': base64.b64encode(output.getvalue()),
            'report_filename': 'all_products_history.xlsx'
        })
