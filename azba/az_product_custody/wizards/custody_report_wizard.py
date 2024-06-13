# -*- coding: utf-8 -*-
import base64
from io import BytesIO
from datetime import datetime
from odoo import fields, models, api
import xlsxwriter


class CustodyReportWizard(models.TransientModel):
    _name = 'custody.report.wizard'
    _description = 'Custody Report Wizard'

    start_date = fields.Datetime(string='Start Date', required=True)
    end_date = fields.Datetime(string='End Date', required=True)
    location_id = fields.Many2one('stock.location', string='Location', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')

    def generate_report(self):
        custody_product_ids = self.env['product.custody'].search([]).mapped('product_id.id')

        domain = [
            ('location_id', '=', self.location_id.id),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('product_id', 'in', custody_product_ids),
            ('state', '=', 'done'),
            '|',  # This is a logical OR operator
            ('picking_id.name', 'ilike', '/out/'),
            ('picking_id.name', 'ilike', '/in/')
        ]

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        else:
            domain.append(('partner_id', '!=', False))

        moves = self.env['stock.move'].search(domain)

        data = {}
        detailed_data = []
        for move in moves:
            partner = f"[{move.partner_id.code}] {move.partner_id.name}"
            product = f"[{move.product_id.product_tmpl_id.code}] {move.product_id.name}"
            if partner not in data:
                data[partner] = {}
            if product not in data[partner]:
                data[partner][product] = {'out': 0, 'in': 0}
            data[partner][product]['out'] += move.product_uom_qty
            if self.partner_id:
                detailed_data.append({
                    'date': move.date,
                    'picking_name': move.picking_id.name,
                    'partner': partner,
                    'product': product,
                    'quantity_out': move.product_uom_qty,
                    'quantity_in': 0,
                    'type': 'out'
                })

        domain_return = [
            ('location_dest_id', '=', self.location_id.id),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('product_id', 'in', custody_product_ids),
            ('state', '=', 'done'),
            '|',  # This is a logical OR operator
            ('picking_id.name', 'ilike', '/out/'),
            ('picking_id.name', 'ilike', '/in/')
        ]
        if self.partner_id:
            domain_return.append(('partner_id', '=', self.partner_id.id))
        else:
            domain_return.append(('partner_id', '!=', False))

        moves_return = self.env['stock.move'].search(domain_return)

        for move in moves_return:
            partner = f"[{move.partner_id.code.strip() if move.partner_id.code else ''}] {move.partner_id.name}"
            product = f"[{move.product_id.product_tmpl_id.code.strip() if move.product_id.product_tmpl_id.code else ''}] {move.product_id.name}"
            if partner not in data:
                data[partner] = {}
            if product not in data[partner]:
                data[partner][product] = {'out': 0, 'in': 0}
            data[partner][product]['in'] += move.product_uom_qty
            if self.partner_id:
                detailed_data.append({
                    'date': move.date,
                    'picking_name': move.picking_id.name,
                    'partner': partner,
                    'product': product,
                    'quantity_out': 0,
                    'quantity_in': move.product_uom_qty,
                    'type': 'in'
                })

        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        worksheet = workbook.add_worksheet()

        if not self.partner_id:
            worksheet.write(0, 0, 'Partner')
            worksheet.write(0, 1, 'Product')
            worksheet.write(0, 2, 'Sum Out')
            worksheet.write(0, 3, 'Sum In')
            worksheet.write(0, 4, 'Balance')

            row = 1
            for partner, products in data.items():
                for product, values in products.items():
                    worksheet.write(row, 0, partner)
                    worksheet.write(row, 1, product)
                    worksheet.write(row, 2, values['out'])
                    worksheet.write(row, 3, values['in'])
                    worksheet.write(row, 4, values['out'] - values['in'])
                    row += 1
        else:
            worksheet.write(0, 0, 'Date')
            worksheet.write(0, 1, 'Picking')
            worksheet.write(0, 2, 'Partner')
            worksheet.write(0, 3, 'Product')
            worksheet.write(0, 4, 'Quantity Out')
            worksheet.write(0, 5, 'Quantity In')
            worksheet.write(0, 6, 'Type')

            row = 1
            for record in detailed_data:
                worksheet.write(row, 0, record['date'].strftime('%Y-%m-%d %H:%M:%S'))
                worksheet.write(row, 1, record['picking_name'])
                worksheet.write(row, 2, record['partner'])
                worksheet.write(row, 3, record['product'])
                worksheet.write(row, 4, record['quantity_out'])
                worksheet.write(row, 5, record['quantity_in'])
                worksheet.write(row, 6, record['type'])
                row += 1

        workbook.close()
        file_data.seek(0)
        file_content = file_data.read()

        attachment = self.env['ir.attachment'].create({
            'name': 'Custody Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_content),
            'store_fname': 'custody_report.xlsx',
            'res_model': 'custody.report.wizard',
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }
