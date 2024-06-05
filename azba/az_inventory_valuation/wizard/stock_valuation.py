from odoo import models, fields, api
import io
import xlsxwriter
import base64
from datetime import time, datetime, timedelta
from collections import defaultdict


class StockValuationWizard(models.TransientModel):
    _name = 'stock.valuation.wizard'
    _description = 'Stock Valuation Wizard'

    date = fields.Datetime(string='Date', required=True)
    report_file = fields.Binary(string='Report File')
    report_filename = fields.Char(string='Report Filename', default='stock_valuation.xlsx')

    def get_stock_valuation(self):
        self.ensure_one()
        date = self.date

        if date.time() == time(0, 0, 0):
            date = date - timedelta(days=1)
            date = date.replace(hour=23, minute=59, second=59, microsecond=0)

        stock_history_model = self.env['stock.quantity.history'].create({
            'inventory_datetime': date
        })

        action = stock_history_model.open_at_date()
        domain = [('create_date', '<=', self.date), ('product_id.type', '=', 'product')]
        # domain += [('company_id', 'in', self.env.user.company_ids.ids)]

        stock_valuation_lines = self.env['stock.valuation.layer'].search(domain)
        # Aggregate quantities by product_id
        product_quantities = defaultdict(float)
        for line in stock_valuation_lines:
            product_quantities[line.product_id.id] += line.quantity

        valuation_lines = []
        for product_id, total_quantity in product_quantities.items():
            product = self.env['product.product'].browse(product_id)
            if product:
                latest_purchase_line = self.env['purchase.order.line'].search([
                    ('product_id', '=', product.id),
                    ('order_id.date_order', '<=', date)
                ], order='date_order desc', limit=1)

                latest_vendor_bill_line = self.env['account.move.line'].search([
                    ('product_id', '=', product.id),
                    ('move_id.invoice_date', '<=', date),
                    ('move_id.move_type', 'in', ['in_invoice', 'in_refund'])
                ], order='date desc', limit=1)

                if latest_purchase_line and latest_vendor_bill_line:
                    purchase_date_order = datetime.combine(latest_purchase_line.order_id.date_order, time.max)
                    vendor_invoice_date = datetime.combine(latest_vendor_bill_line.move_id.invoice_date, time.max)

                    if purchase_date_order >= vendor_invoice_date:
                        price = latest_purchase_line.price_unit
                    else:
                        price = latest_vendor_bill_line.price_unit
                elif latest_purchase_line:
                    price = latest_purchase_line.price_unit
                elif latest_vendor_bill_line:
                    price = latest_vendor_bill_line.price_unit
                else:
                    price = 0.0

                value = total_quantity * price
                code = f'{product.product_tmpl_id.code.strip()}' if product.product_tmpl_id.code else '[]'

                valuation_lines.append({
                    'product_code': code,
                    'product': product.name,
                    'latest_purchase_price': price,
                    'quantity': total_quantity,
                    'uom': product.uom_id.name,
                    'value': value,
                })

        self._generate_excel_report(valuation_lines)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Valuation',
            'view_mode': 'form',
            'res_model': 'stock.valuation.wizard',
            'res_id': self.id,
            'target': 'new',
        }

    def _generate_excel_report(self, valuation_lines):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Stock Valuation')

        headers = ['Code', 'Product', 'Latest Purchase Price', 'Quantity', 'Value', 'Unit of Measure']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        for row_num, line in enumerate(valuation_lines, start=1):
            worksheet.write(row_num, 0, line['product_code'])
            worksheet.write(row_num, 1, line['product'])
            worksheet.write(row_num, 2, line['latest_purchase_price'])
            worksheet.write(row_num, 3, line['quantity'])
            worksheet.write(row_num, 4, line['value'])
            worksheet.write(row_num, 5, line['uom'])

        workbook.close()
        output.seek(0)

        self.report_file = base64.b64encode(output.read())
        self.report_filename = 'stock_valuation_{}.xlsx'.format(fields.Date.today())

    def download_report(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=stock.valuation.wizard&id={}&field=report_file&filename_field=report_filename&download=true'.format(
                self.id),
            'target': 'new',
        }
