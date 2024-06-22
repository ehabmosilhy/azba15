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

    def _get_previous_balance(self):
        """Get the previous balance of the partner before the start date."""
        custody_product_ids = self.env['product.custody'].search([]).mapped('product_id.id')
        previous_balances = {product_id: 0 for product_id in custody_product_ids}

        domain_out = [
            ('location_id', '=', self.location_id.id),
            ('date', '<', self.start_date),
            ('product_id', 'in', custody_product_ids),
            ('state', '=', 'done'),
            ('picking_id.picking_type_id.code', '=', 'outgoing')
        ]
        domain_in = [
            ('location_dest_id', '=', self.location_id.id),
            ('date', '<', self.start_date),
            ('product_id', 'in', custody_product_ids),
            ('state', '=', 'done'),
            ('picking_id.picking_type_id.code', '=', 'incoming')
        ]

        if self.partner_id:
            domain_out.append(('partner_id', '=', self.partner_id.id))
            domain_in.append(('partner_id', '=', self.partner_id.id))
        else:
            domain_out.append(('partner_id', '!=', False))
            domain_in.append(('partner_id', '!=', False))

        moves_out = self.env['stock.move'].search(domain_out)
        moves_in = self.env['stock.move'].search(domain_in)

        for move in moves_out:
            previous_balances[move.product_id.id] += move.product_uom_qty

        for move in moves_in:
            previous_balances[move.product_id.id] -= move.product_uom_qty

        return previous_balances

    def _prepare_report_data(self):
        custody_product_ids = self.env['product.custody'].search([]).mapped('product_id.id')

        domain = [
            ('location_id', '=', self.location_id.id),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('product_id', 'in', custody_product_ids),
            ('state', '=', 'done')
        ]

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))
        else:
            domain.append(('partner_id', '!=', False))

        moves = self.env['stock.move'].search(domain, order='product_id')

        data = []
        data_dict = {}
        detailed_data = []

        previous_balances = self._get_previous_balance()
        end_balances = previous_balances.copy()

        for move in moves:
            partner = f"[{move.partner_id.code}] {move.partner_id.name}" if move.partner_id else ''
            product = f"[{move.product_id.product_tmpl_id.code.strip() if move.product_id.product_tmpl_id.code else ''}] {move.product_id.name}"
            if partner not in data_dict:
                data_dict[partner] = {}
            if product not in data_dict[partner]:
                data_dict[partner][product] = {'out': 0, 'in': 0, 'previous_balance': previous_balances[move.product_id.id]}

            if move.picking_id.picking_type_id.code == 'outgoing':
                data_dict[partner][product]['out'] += move.product_uom_qty
                end_balances[move.product_id.id] += move.product_uom_qty
                if self.partner_id:
                    detailed_data.append({
                        'date': move.date,
                        'picking_name': move.picking_id.name,
                        'partner': partner,
                        'product': product,
                        'quantity_out': move.product_uom_qty,
                        'quantity_in': 0,
                        'previous_balance': previous_balances[move.product_id.id],
                        'end_balance': end_balances[move.product_id.id]
                    })
                    previous_balances[move.product_id.id] = end_balances[move.product_id.id]
            elif move.picking_id.picking_type_id.code == 'incoming':
                data_dict[partner][product]['in'] += move.product_uom_qty
                end_balances[move.product_id.id] -= move.product_uom_qty
                if self.partner_id:
                    detailed_data.append({
                        'date': move.date,
                        'picking_name': move.picking_id.name,
                        'partner': partner,
                        'product': product,
                        'quantity_out': 0,
                        'quantity_in': move.product_uom_qty,
                        'previous_balance': previous_balances[move.product_id.id],
                        'end_balance': end_balances[move.product_id.id]
                    })
                    previous_balances[move.product_id.id] = end_balances[move.product_id.id]

        domain_return = [
            ('location_dest_id', '=', self.location_id.id),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date),
            ('product_id', 'in', custody_product_ids),
            ('state', '=', 'done')
        ]

        if self.partner_id:
            domain_return.append(('partner_id', '=', self.partner_id.id))
        else:
            domain_return.append(('partner_id', '!=', False))

        moves_return = self.env['stock.move'].search(domain_return)

        for move in moves_return:
            partner = f"[{move.partner_id.code.strip() if move.partner_id.code else ''}] {move.partner_id.name}" if move.partner_id else ''
            product = f"[{move.product_id.product_tmpl_id.code.strip() if move.product_id.product_tmpl_id.code else ''}] {move.product_id.name}"
            if partner not in data_dict:
                data_dict[partner] = {}
            if product not in data_dict[partner]:
                data_dict[partner][product] = {'out': 0, 'in': 0, 'previous_balance': previous_balances[move.product_id.id]}

            if move.picking_id.picking_type_id.code == 'incoming':
                data_dict[partner][product]['in'] += move.product_uom_qty
                end_balances[move.product_id.id] -= move.product_uom_qty
                if self.partner_id:
                    detailed_data.append({
                        'date': move.date,
                        'picking_name': move.picking_id.name,
                        'partner': partner,
                        'product': product,
                        'quantity_out': 0,
                        'quantity_in': move.product_uom_qty,
                        'previous_balance': previous_balances[move.product_id.id],
                        'end_balance': end_balances[move.product_id.id]
                    })
                    previous_balances[move.product_id.id] = end_balances[move.product_id.id]
            elif move.picking_id.picking_type_id.code == 'outgoing':
                data_dict[partner][product]['out'] += move.product_uom_qty
                end_balances[move.product_id.id] += move.product_uom_qty
                if self.partner_id:
                    detailed_data.append({
                        'date': move.date,
                        'picking_name': move.picking_id.name,
                        'partner': partner,
                        'product': product,
                        'quantity_out': move.product_uom_qty,
                        'quantity_in': 0,
                        'previous_balance': previous_balances[move.product_id.id],
                        'end_balance': end_balances[move.product_id.id]
                    })
                    previous_balances[move.product_id.id] = end_balances[move.product_id.id]

        for partner, products in data_dict.items():
            for product, values in products.items():
                data.append({
                    'partner': partner,
                    'product': product,
                    'out': values['out'],
                    'in': values['in'],
                    'balance': values['out'] - values['in'],
                    'previous_balance': values['previous_balance']
                })

        return data, detailed_data

    def generate_pdf_report(self):
        data, detailed_data = self._prepare_report_data()
        datas = {
            "wizard": self.read()[0],  # This includes the 'docs'
            "data": detailed_data if self.partner_id else data
        }
        return self.env.ref('az_product_custody.custody_report_pdf_action').report_action(self, data=datas)
