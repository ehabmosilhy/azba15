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
            ('product_id', 'in', custody_product_ids)
        ]
        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

        pickings = self.env['stock.move'].search(domain)

        data = {}
        for pick in pickings:
            partner = pick.partner_id.name
            for move in pick.move_ids_without_package.filtered(lambda m: m.state == 'done'):
                product = move.product_id.name
                if move.product_id.id not in custody_product_ids:
                    continue
                if partner not in data:
                    data[partner] = {}
                if product not in data[partner]:
                    data[partner][product] = {'out': 0, 'in': 0}
                data[partner][product]['out'] += move.qty_done

        domain_return = [
            ('location_dest_id', '=', self.location_id.id),
            ('scheduled_date', '>=', self.start_date),
            ('scheduled_date', '<=', self.end_date),
            ('move_ids_without_package.product_id', 'in', custody_product_ids)
        ]
        if self.partner_id:
            domain_return.append(('partner_id', '=', self.partner_id.id))

        pickings_return = self.env['stock.picking'].search(domain_return)

        for pick in pickings_return:
            partner = pick.partner_id.name
            for move in pick.move_ids_without_package.filtered(lambda m: m.state == 'done'):
                product = move.product_id.name
                if move.product_id.id not in custody_product_ids:
                    continue
                if partner not in data:
                    data[partner] = {}
                if product not in data[partner]:
                    data[partner][product] = {'out': 0, 'in': 0}
                data[partner][product]['in'] += move.product_uom_qty

        file_data = BytesIO()
        workbook = xlsxwriter.Workbook(file_data)
        worksheet = workbook.add_worksheet()

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