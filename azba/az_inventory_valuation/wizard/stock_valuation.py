from odoo import models, fields, api
import io
import xlsxwriter
import base64
from datetime import datetime, time


class StockValuationWizard(models.TransientModel):
    _name = 'stock.valuation.wizard'
    _description = 'Stock Valuation Wizard'

    date = fields.Date(string='Date', required=True)
    report_file = fields.Binary(string='Report File')
    report_filename = fields.Char(string='Report Filename', default='stock_valuation.xlsx')

    def get_stock_valuation(self):
        self.ensure_one()
        date = self.date

        # SQL query to fetch summed quantities and values from stock_valuation_layer
        query = """
        SELECT
            product_id as product_id,
            SUM(quantity) as total_quantity,
            SUM(value) as total_value
        FROM
            stock_valuation_layer
        WHERE
            create_date <= %s AND
            company_id in %s
        GROUP BY
            product_id;
        """
        self.env.cr.execute(query, (date, tuple(self.env.user.company_ids.ids)))
        result = self.env.cr.dictfetchall()

        # Fetch all products at once
        product_ids = [res['product_id'] for res in result]
        products = {prod.id: prod for prod in self.env['product.product'].browse(product_ids)}

        valuation_lines = []
        for res in result:
            product = products.get(res['product_id'])
            if product:
                # Fetch the latest purchase price before or on the given date from purchase order lines
                latest_purchase_line = self.env['purchase.order.line'].search([
                    ('product_id', '=', product.id),
                    ('order_id.date_order', '<=', date)
                ], order='date_order desc', limit=1)

                # Fetch the latest purchase price before or on the given date from vendor bill lines
                latest_vendor_bill_line = self.env['account.move.line'].search([
                    ('product_id', '=', product.id),
                    ('move_id.invoice_date', '<=', date),
                    ('move_id.move_type', 'in', ['in_invoice', 'in_refund'])  # Consider vendor bills and refunds
                ], order='date desc', limit=1)

                # Determine the latest price from either purchase order line or vendor bill line


                # Fetch the latest purchase price before or on the given date from purchase order lines

                # Fetch the latest purchase price before or on the given date from purchase order lines
                latest_purchase_line = self.env['purchase.order.line'].search([
                    ('product_id', '=', product.id),
                    ('order_id.date_order', '<=', date)
                ], order='date_order desc', limit=1)

                # Fetch the latest purchase price before or on the given date from vendor bill lines
                latest_vendor_bill_line = self.env['account.move.line'].search([
                    ('product_id', '=', product.id),
                    ('move_id.invoice_date', '<=', date),
                    ('move_id.move_type', 'in', ['in_invoice', 'in_refund'])  # Consider vendor bills and refunds
                ], order='date desc', limit=1)

                # Determine the latest price from either purchase order line or vendor bill line
                if latest_purchase_line and latest_vendor_bill_line:
                    # Convert date_order to datetime with the last possible time of the day
                    purchase_date_order = datetime.combine(latest_purchase_line.order_id.date_order, time.max)
                    # Convert invoice_date to datetime with the last possible time of the day
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


                value = res['total_quantity'] * price
                code = f'{product.product_tmpl_id.code.strip()}' if product.product_tmpl_id.code else '[]'

                # Include product code and latest purchase price in the results
                valuation_lines.append({
                    'product_code':code,
                    'product': product.name,
                    'latest_purchase_price': price,
                    'quantity': res['total_quantity'],
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
        headers = ['Product', 'Product Code', 'Latest Purchase Price', 'Quantity', 'Unit of Measure', 'Value']
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)

        # Write data to the sheet
        for row_num, line in enumerate(valuation_lines, start=1):
            worksheet.write(row_num, 0, line['product'])
            worksheet.write(row_num, 1, line['product_code'])
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
