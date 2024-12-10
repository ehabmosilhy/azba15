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
    product_id = fields.Many2one('product.product', string='Product', domain=[('type', '=', 'product')])
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
        return self.env['stock.move'].search(domain, order='date asc')

    def _calculate_adjustment_difference(self, move):
        """Calculate the actual adjustment difference from the previous balance."""
        if not move.picking_id:  # This is an adjustment move
            # Get the balance just before this adjustment
            domain = [
                ('create_date', '<', move.date),
                ('product_id', '=', move.product_id.id)
            ]
            previous_layers = self.env['stock.valuation.layer'].search(domain)
            previous_balance = sum(layer.quantity for layer in previous_layers)
            
            # The new quantity set by the adjustment
            new_quantity = sum(layer.quantity for layer in move.stock_valuation_layer_ids)
            
            # The adjustment is the difference
            return new_quantity - previous_balance
        return 0

    def action_generate_report(self):
        initial_balances = self.get_product_balance(self.start_date)
        final_balances = self.get_product_balance(self.end_date)

        # Combine data for report
        report_data = []
        
        # Get products based on selection
        domain = [('type', '=', 'product')]
        if self.product_id:
            domain.append(('id', '=', self.product_id.id))
        products = self.env['product.product'].search(domain)
        
        for product in products:
            # Get moves within period
            period_moves = self._get_stock_moves(product, self.start_date, self.end_date)
            
            total_in = 0
            total_out = 0
            total_adjustments = 0
            current_qty = next((item['quantity'] for item in initial_balances if item['product_id'] == product.id), 0.0)
            
            print("\n=== Processing Movements for Product:", product.display_name, "===")
            print(f"Initial Balance: {current_qty}")
            
            # Calculate in/out quantities and adjustments move by move
            for move in period_moves:
                if move.picking_id:  # Non-adjustment moves
                    picking_code = move.picking_type_id.code
                    if picking_code == 'incoming':
                        total_in += move.product_qty
                        current_qty += move.product_qty
                        print(f"IN  Movement: {move.picking_id.name} - Type: {picking_code} - Qty: {move.product_qty} - Running Total: {current_qty} - From: {move.location_id.name} -> To: {move.location_dest_id.name}")
                    elif picking_code in ['outgoing','mrp_operation']:  
                        total_out += move.product_qty
                        current_qty -= move.product_qty
                        print(f"OUT Movement: {move.picking_id.name} - Type: {picking_code} - Qty: {move.product_qty} - Running Total: {current_qty} - From: {move.location_id.name} -> To: {move.location_dest_id.name}")
                    else:  # internal transfers
                        print(f"INTERNAL Movement: {move.picking_id.name} - Type: {picking_code} - Qty: {move.product_qty} - Running Total: {current_qty} - From: {move.location_id.name} -> To: {move.location_dest_id.name}")
                else:  # Adjustment moves
                    # expected_qty = current_qty
                    # actual_qty = move.product_qty
                    # adjustment = actual_qty - expected_qty
                    # total_adjustments += adjustment
                    # current_qty = actual_qty  # Update current_qty to the adjusted quantity
                    # print(f"ADJ Movement: Expected: {expected_qty}, Actual: {actual_qty}, Adjustment: {adjustment} - Running Total: {current_qty} - From: {move.location_id.name} -> To: {move.location_dest_id.name}")
                    if move.location_id.id == move.location_dest_id.id:
                        total_adjustments += move.product_qty
                    else:
                        total_adjustments -= move.product_qty

            print(f"\nFinal Totals for {product.display_name}:")
            print(f"Total IN: {total_in}")
            print(f"Total OUT: {total_out}")
            print(f"Total Adjustments: {total_adjustments}")
            print("=" * 50)
            
            # Find initial and final balances
            initial_balance = next((item['quantity'] for item in initial_balances if item['product_id'] == product.id), 0.0)
            final_balance = next((item['quantity'] for item in final_balances if item['product_id'] == product.id), 0.0)

            # Only include products with activity or balance
            if initial_balance != 0 or final_balance != 0 or total_in != 0 or total_out != 0 or total_adjustments != 0:
                code = f'{product.product_tmpl_id.code.strip()}' if product.product_tmpl_id.code else '[]'
                report_data.append({
                    'product_code': code,
                    'product_name': product.name,
                    'initial_balance': initial_balance,
                    'total_in': total_in,
                    'total_out': total_out,
                    'total_adjustments': total_adjustments,
                    'final_balance': final_balance,
                })

        # Sort report data by product code
        report_data = sorted(report_data, key=lambda x: x['product_code'] or '')

        self._generate_excel_report(report_data)
        return {
            'type': 'ir.actions.act_window',
            'name': 'All-Product History Report',
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
        headers = ['Product Code', 'Product Name', 'Initial Balance', 'Total In', 'Total Out', 'Total Adjustments', 'Final Balance']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Write data
        for row_num, line in enumerate(report_data, start=1):
            worksheet.write(row_num, 0, line['product_code'])
            worksheet.write(row_num, 1, line['product_name'])
            worksheet.write(row_num, 2, line['initial_balance'])
            worksheet.write(row_num, 3, line['total_in'])
            worksheet.write(row_num, 4, line['total_out'])
            worksheet.write(row_num, 5, line['total_adjustments'])
            worksheet.write(row_num, 6, line['final_balance'])

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
