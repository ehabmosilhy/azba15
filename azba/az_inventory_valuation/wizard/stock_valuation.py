from odoo import models, fields, api
import io
import xlsxwriter
import base64

class StockValuationWizard(models.TransientModel):
    _name = 'stock.valuation.wizard'
    _description = 'Stock Valuation Wizard'

    date = fields.Date(string='Date', required=True)
    report_file = fields.Binary(string='Report File')
    report_filename = fields.Char(string='Report Filename', default='stock_valuation.xlsx')

    def get_stock_valuation(self):
        self.ensure_one()
        date = self.date

        products = self.env['product.product'].search([])
        valuation_lines = []

        for product in products:
            quantity = sum(self.env['stock.quant'].search([
                ('product_id', '=', product.id),
                ('location_id.usage', '=', 'internal')
            ]).mapped('quantity'))

            latest_purchase_line = self.env['purchase.order.line'].search([
                ('product_id', '=', product.id)
            ], order='date_order desc', limit=1)

            price = latest_purchase_line.price_unit if latest_purchase_line else 0.0
            value = quantity * price
            name_and_code = f'[{product.product_tmpl_id.code.strip()}] {product.name}' if product.product_tmpl_id.code else product.name
            valuation_lines.append({
                'product': name_and_code,
                'quantity': quantity,
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

        # Define the headers
        headers = ['Product', 'Quantity', 'Unit of Measure', 'Value']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Write data to the sheet
        for row_num, line in enumerate(valuation_lines, start=1):
            worksheet.write(row_num, 0, line['product'])
            worksheet.write(row_num, 1, line['quantity'])
            worksheet.write(row_num, 2, line['uom'])
            worksheet.write(row_num, 3, line['value'])

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
class StockValuationResult(models.TransientModel):
    _name = 'stock.valuation.result'
    _description = 'Stock Valuation Result'

    product = fields.Char(string='Product')
    quantity = fields.Float(string='Quantity')
    uom = fields.Char(string='Unit of Measure')
    value = fields.Float(string='Value')
