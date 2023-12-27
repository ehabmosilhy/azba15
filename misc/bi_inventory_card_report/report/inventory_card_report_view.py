# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields,  _
import operator
from datetime import datetime,date
from odoo.tools.float_utils import float_round

class StockCardReportTemplate(models.AbstractModel):
    _name = 'report.bi_inventory_card_report.inventory_card_report_template'
    _description = 'Stock Card Report Template'


    def _get_product_detail(self, data):
        start_date_data = data.get('date_from')
        end_date_data = data.get('date_to')
        product_ids = data.get('product_ids')
        product_category_ids = data.get('product_category_ids')
        report_by = data.get('report_by')
        if report_by == 'product_category':
            product_ids = self.env['product.product'].search([('categ_id', 'in', product_category_ids.ids)])
            lines  = []
            for product in product_ids:         
                move_line_ids =self.env['stock.move.line'].search([('move_id.date','>=', start_date_data),('move_id.date','<=', end_date_data),('state','=', 'done'),('product_id','=',product.id),
                                                    '|',('location_id','=',data.get('location_id').id) , 
                                                    ('location_dest_id','=',data.get('location_id').id)
                                                   ])


                balance = 0.0
                for stock_move in move_line_ids:
                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('location_id.usage', '=', 'inventory')]):
                        if move:
                            move_date = move.date
                            if move.qty_done:
                                balance = balance + move.qty_done
                                lines.append({'origin': 'Inventory Adjustment', 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done, 'balance': balance, 'out_qty': 0.0, 'category': move.product_id.categ_id})
                    
                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('picking_type_id.code','=', 'incoming'), '|',('move_id.warehouse_id', '=', data.get('warehouse_id').id), ('move_id.warehouse_id', '=', False)]):
                        if move:
                            move_date = move.date
                            if move.qty_done:
                                balance = balance + move.qty_done
                                if move.origin:
                                    lines.append({'origin': move.origin, 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done, 'balance': balance, 'out_qty': 0.0, 'category': move.product_id.categ_id})
                                else: 
                                    lines.append({'origin': move.reference, 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done, 'balance': balance, 'out_qty': 0.0, 'category': move.product_id.categ_id})
                    
                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('picking_type_id.code','=', 'outgoing'), '|',('move_id.warehouse_id', '=', data.get('warehouse_id').id), ('move_id.warehouse_id', '=', False)]):
                        if move:
                            move_date = move.date
                            if move.qty_done:
                                balance = balance - move.qty_done
                                if move.origin:
                                    lines.append({'origin': move.origin, 'move_date': move_date,'out_qty': move.qty_done,'product_id':move.product_id, 'balance': balance, 'in_qty':0.0, 'category': move.product_id.categ_id})
                                else:
                                    lines.append({'origin': move.reference, 'move_date': move_date,'out_qty': move.qty_done,'product_id':move.product_id, 'balance': balance, 'in_qty':0.0, 'category': move.product_id.categ_id})
            sorted_lines = sorted(lines, key=lambda x: x['move_date'], reverse=False)
            return sorted_lines
        else:
            product_ids = self.env['product.product'].search([('id', 'in', product_ids.ids)])
            lines = []
            for product in product_ids:
                move_line_ids =self.env['stock.move.line'].search([('move_id.date','>=', start_date_data),('state','=', 'done'),('move_id.date','<=', end_date_data),('product_id','=',product.id),
                                                    '|',('location_id','=',data.get('location_id').id) , 
                                                    ('location_dest_id','=',data.get('location_id').id),
                                                   ])


                balance = 0.0
                for stock_move in move_line_ids:
                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('location_id.usage', '=', 'inventory')]):
                        if move:
                            move_date = move.date
                            if move.qty_done:
                                lines.append({'origin': 'Inventory Adjustment', 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done,'out_qty': 0.0})
                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('picking_type_id.code','=', 'incoming'), '|',('move_id.warehouse_id', '=', data.get('warehouse_id').id), ('move_id.warehouse_id', '=', False)]):
                        if move:
                            move_date = move.date
                            if move.qty_done:
                                if move.origin:
                                    lines.append({'origin': move.origin, 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done, 'out_qty': 0.0})
                                else: 
                                    lines.append({'origin': move.reference, 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done, 'out_qty': 0.0})
                    
                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('picking_type_id.code','=', 'outgoing'), '|',('move_id.warehouse_id', '=', data.get('warehouse_id').id), ('move_id.warehouse_id', '=', False)]):
                        if move:
                            move_date = move.date
                            if move.qty_done:
                                if move.origin:
                                    lines.append({'origin': move.origin, 'move_date': move_date,'out_qty': move.qty_done,'product_id':move.product_id, 'in_qty':0.0})
                                else:
                                    lines.append({'origin': move.reference, 'move_date': move_date, 'product_id': move.product_id,'out_qty':move.qty_done, 'in_qty': 0.0})
            sorted_lines = sorted(lines, key=lambda x: x['move_date'], reverse=False)
            return sorted_lines


    @api.model
    def _get_report_values(self, docids, data=None):
        report_by = data['form']['report_by']
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        product_ids = self.env['product.product'].browse(data['form']['product_ids'])
        product_category_ids = self.env['product.category'].browse(data['form']['product_category_ids'])
        if data['form'].get('company_id'):
            company_id = self.env['res.company'].browse(data['form']['company_id'][0])
        else:
            company_id = False
        if data['form'].get('location_id'):
            location_id = self.env['stock.location'].browse(data['form']['location_id'][0])
        else:
            location_id = False
        if data['form'].get('warehouse_id'):
            warehouse_id = self.env['stock.warehouse'].browse(data['form']['warehouse_id'][0])
        else:
            warehouse_id = False
        if data['form'].get('location_id'):
            location_id = self.env['stock.location'].browse(data['form']['location_id'][0])
        else:
            location_id = False

        data  = { 
            'report_by'         : report_by,
            'date_from'         : date_from,
            'date_to'           : date_to,
            'product_ids'       : product_ids,
            'company_id'        : company_id,
            'location_id'       : location_id,
            'warehouse_id'      : warehouse_id,
            'product_category_ids' : product_category_ids
        }
        docargs = {
                   'doc_model': 'stock.card.report',
                   'data': data,
                   'get_product_detail':self._get_product_detail,
                   }
        return docargs 
