from odoo import models, fields, api
import io
import xlsxwriter
import base64
from datetime import datetime, timedelta
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

        if date.time() == datetime.min.time():
            date = date - timedelta(days=1)
            date = date.replace(hour=23, minute=59, second=59, microsecond=0)

        stock_history_model = self.env['stock.quantity.history'].create({
            'inventory_datetime': date
        })

        action = stock_history_model.open_at_date()
        domain = [('create_date', '<=', self.date), ('product_id.type', '=', 'product')]

        stock_valuation_lines = self.env['stock.valuation.layer'].search(domain)
        product_quantities = defaultdict(float)
        for line in stock_valuation_lines:
            product_quantities[line.product_id.id] += line.quantity

        valuation_lines = []
        for product_id, total_quantity in product_quantities.items():
            product = self.env['product.product'].browse(product_id)
            if product:
                latest_vendor_bill_line = self.env['account.move.line'].search([
                    ('product_id', '=', product.id),
                    ('move_id.invoice_date', '<=', date),
                    ('move_id.move_type', 'in', ['in_invoice', 'in_refund'])
                ], order='date desc', limit=1)

                price = 0.0
                last_purchase_document_id = None

                if latest_vendor_bill_line:
                    price = latest_vendor_bill_line.price_unit
                    last_purchase_document_id = latest_vendor_bill_line.move_id.name

                value = total_quantity * price
                code = f'{product.product_tmpl_id.code.strip()}' if product.product_tmpl_id.code else '[]'

                valuation_lines.append({
                    'product_code': code,
                    'product': product.name,
                    'latest_purchase_price': price,
                    'quantity': total_quantity,
                    'uom': product.uom_id.name,
                    'value': value,
                    'last_purchase_document_id': last_purchase_document_id,
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

        headers = ['Code', 'Product', 'Latest Purchase Price', 'Quantity', 'Value', 'Unit of Measure', 'Last Purchase Document ID']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        for row_num, line in enumerate(valuation_lines, start=1):
            worksheet.write(row_num, 0, line['product_code'])
            worksheet.write(row_num, 1, line['product'])
            worksheet.write(row_num, 2, line['latest_purchase_price'])
            worksheet.write(row_num, 3, line['quantity'])
            worksheet.write(row_num, 4, line['value'])
            worksheet.write(row_num, 5, line['uom'])
            worksheet.write(row_num, 6, line['last_purchase_document_id'])

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
