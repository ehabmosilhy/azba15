# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import base64
import io
from io import BytesIO
import xlwt
import csv

class InventoryCardReport(models.TransientModel):
    _name = "inventory.card.report"
    _description = "Inventory Card Report"
    _rec_name = 'report_by'

    date_from = fields.Date('Start Date')
    date_to = fields.Date('End Date')
    company_id = fields.Many2one('res.company', string="Company", required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse", required=True,)
    location_id = fields.Many2one('stock.location', string="Location",required=True,)
    report_by = fields.Selection([('product', 'Product'),
                                ('product_category', 'Product Category'),
                                ], string='Report By', required=True, default='product')
    product_ids = fields.Many2many('product.product',string="Product")
    product_category_ids= fields.Many2many('product.category',string="Product Category")
    is_on_hand_only = fields.Boolean('On Hand Only')
    @api.onchange('warehouse_id')
    def _onchange_warehouse(self):
        if self.warehouse_id:
            self.update({
                'company_id':self.warehouse_id.company_id.id,
            })

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_to < record.date_from:
                    raise ValidationError("End date must be greater than start date!")

    def stock_card_pdf_report(self):
        [data] = self.read()
        datas = {
             'ids': [1],
             'model': 'inventory.card.report',
             'form': data
        }
        action = self.env.ref('bi_inventory_card_report.inventory_card_report_action_view').report_action(self, data=datas)
        return action

    def stock_card_xls(self):
        data ={
                'form': self.read()[0],
             
        }
        filename = 'Inventory Card Report.xls'
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet("Sheet 1", cell_overwrite_ok = True )
        worksheet.col(0).width = 5000
        style_header = xlwt.easyxf(
            "font:height 300; font: name Liberation Sans, bold on,color black; align: vert centre, horiz center;pattern: pattern solid, pattern_fore_colour gray25;")

        style_line_heading = xlwt.easyxf("font: name Liberation Sans, bold on;align: horiz centre; pattern: pattern solid, pattern_fore_colour gray25;")
        worksheet.row(0).height_mismatch = True
        worksheet.row(0).height = 500
        worksheet.col(0).width = 6000
        worksheet.col(1).width = 6000
        worksheet.col(2).width = 6000
        worksheet.col(3).width = 6000
        worksheet.col(4).width = 6000
        line = 1
        if self.report_by == 'product':
            worksheet.write_merge(0, 1, 0, 4, "Inventory Card Report - Product\n", style=style_header)
        else: 
            worksheet.write_merge(0, 1, 0, 4, "Inventory Card Report - Product Category\n", style=style_header)
        line += 2
        for i in data:
            worksheet.write_merge(line,line,0,1, 'Start Date', style = style_line_heading)
            worksheet.write_merge(line,line,3,4, 'End Date', style = style_line_heading)
            worksheet.write_merge(line+1,line+1, 0,1, str(self.date_from), style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
            worksheet.write_merge(line+1,line+1, 3,4, str(self.date_to), style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
          
        

        line += 2
        warehouse_id = self.env['stock.warehouse'].search([('id','=',self.warehouse_id.id)])
        location_id  = self.env['stock.location'].search([('id','=',self.location_id.id)])
        context = self._context
        current_uid = context.get('uid')
        user = self.env['res.users'].browse(current_uid)

        worksheet.write(line,0, 'User', style = style_line_heading)
        worksheet.write_merge(line,line,1,2, 'Warehouse', style = style_line_heading)
        worksheet.write_merge(line,line,3,4, 'Location', style = style_line_heading)

     
      
        worksheet.write(line+1, 0, user.name, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))   
        worksheet.write_merge(line+1,line+1, 1,2, warehouse_id.name, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
        worksheet.write_merge(line+1,line+1, 3,4, location_id.name, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;\n"))

        line  += 3
        for i in data:
            worksheet.write(line,0, 'Date', style = style_line_heading)
            worksheet.write(line,1, 'Origin', style = style_line_heading)
            worksheet.write(line,2, 'In Quantity', style = style_line_heading)
            worksheet.write(line,3, 'Out Quantity', style = style_line_heading)
            worksheet.write(line,4, 'Balance', style = style_line_heading)

        line  += 2
        
        if self.report_by == 'product_category':
            product_category_ids = self.env['product.category'].search([('id','in',self.product_category_ids.ids)])
            product_ids = self.env['product.product'].search([('categ_id', 'in', product_category_ids.ids)])
            lines  = []
            for product in product_ids:         
                move_line_ids =self.env['stock.move.line'].search([('move_id.date','>=', self.date_from),('move_id.date','<=', self.date_to),('state','=','done'),('product_id','=',product.id),
                                                    '|',('location_id','=',self.location_id.id) , 
                                                    ('location_dest_id','=',self.location_id.id)
                                                   ])
                balance = 0.0
                for stock_move in move_line_ids:
                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('location_id.usage', '=', 'inventory')]):
                        if move:
                            move_date = move.date
                            lines.append({'origin': 'Inventory Adjustment', 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done, 'out_qty': 0.0, 'category': move.product_id.categ_id})

                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('picking_type_id.code','=', 'incoming'), '|',('move_id.warehouse_id', '=', self.warehouse_id.id), ('move_id.warehouse_id', '=', False)]):
                        if move:
                            move_date = move.date
                            if move.origin:
                                lines.append({'origin': move.origin, 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done,'out_qty': 0.0, 'category': move.product_id.categ_id,})
                            else: 
                                lines.append({'origin': move.reference, 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done, 'out_qty': 0.0, 'category': move.product_id.categ_id,})
                
                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('picking_type_id.code','=', 'outgoing'), '|',('move_id.warehouse_id', '=',self.warehouse_id.id), ('move_id.warehouse_id', '=', False)]):
                        if move:
                            move_date = move.date
                            if move.origin:
                                lines.append({'origin': move.origin, 'move_date': move_date,'out_qty': move.qty_done,'product_id':move.product_id, 'in_qty':0.0, 'category': move.product_id.categ_id,})
                            else:
                               lines.append({'origin': move.reference, 'move_date': move_date,'out_qty': move.qty_done,'product_id':move.product_id, 'in_qty':0.0, 'category': move.product_id.categ_id,})

            sorted_lines = sorted(lines, key=lambda x: x['move_date'], reverse=False)

            category = []
            for rec in sorted_lines:
                category.append(rec['category'])
            line_categ = line
            for categ in set(category):
                if categ:
                    worksheet.write_merge(line_categ,line_categ,0,4, categ.complete_name, style=xlwt.easyxf("font: name Liberation Sans, bold on;align: horiz centre; pattern: pattern solid, pattern_fore_colour light_orange;"))
                product = []
                for rec in sorted_lines:
                    product.append(rec['product_id'])
                line_pro = line_categ
                for product_id in set(product):
                    if categ.id == product_id.categ_id.id:
                        worksheet.write_merge(line_pro+1,line_pro+1,0,4, product_id.display_name, style=xlwt.easyxf("font: name Liberation Sans, bold on;align: horiz centre; pattern: pattern solid, pattern_fore_colour light_blue;"))
                        line = line_pro + 2
                        worksheet.write_merge(line, line, 0, 3, 'Opening Balance',style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                        worksheet.write(line, 4, '0', style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                        total_in_qty = 0.0
                        total_out_qty = 0.0
                        total_balance = 0.0
                        balance = 0.0
                        line = line + 1 
                        for rec in sorted_lines:
                            if product_id.id == rec['product_id'].id:
                                worksheet.write(line, 0, rec['move_date'].strftime('%m-%d-%Y'), style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                                worksheet.write(line, 1, rec['origin'], style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                                worksheet.write(line, 2, rec['in_qty'], style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                                worksheet.write(line, 3, rec['out_qty'], style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                                balance += rec['in_qty']
                                balance -= rec['out_qty']
                                worksheet.write(line, 4, balance, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                                line += 1
                                total_in_qty += rec['in_qty']
                                total_out_qty += rec['out_qty']
                                total_balance = total_in_qty - total_out_qty
                        worksheet.write(line, 0, ' ', style=xlwt.easyxf("font: name Liberation Sans; align: horiz center; pattern: pattern solid, pattern_fore_colour gray50;"))
                        worksheet.write(line, 1, 'Total', style=xlwt.easyxf("font: name Liberation Sans; align: horiz center; pattern: pattern solid, pattern_fore_colour gray50;"))
                        worksheet.write(line, 2, total_in_qty, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center; pattern: pattern solid, pattern_fore_colour gray50;"))
                        worksheet.write(line, 3, total_out_qty, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center; pattern: pattern solid, pattern_fore_colour gray50;"))
                        worksheet.write(line, 4, total_balance, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center; pattern: pattern solid, pattern_fore_colour gray50;"))
                    line_pro = line + 1
                line_categ = line + 1
                            
        else:
            product_ids = self.env['product.product'].search([('id','in', self.product_ids.ids)])
            lines = []
            for product in product_ids:
                move_line_ids =self.env['stock.move.line'].search([('date','>=', self.date_from),('date','<=', self.date_to), ('state','=','done'),('product_id','=',product.id),
                                                    '|',('location_id','=',self.location_id.id) , 
                                                    ('location_dest_id','=',self.location_id.id),
                                                   ])
                balance = 0.0
                for stock_move in move_line_ids:
                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('location_id.usage', '=', 'inventory')]):
                        if move:
                            move_date = move.date
                            lines.append({'origin': 'Inventory Adjustment', 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done,'out_qty': 0.0})

                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('picking_type_id.code','=', 'incoming'), '|',('move_id.warehouse_id', '=',self.warehouse_id.id), ('move_id.warehouse_id', '=', False)]):
                        if move:
                            move_date = move.date
                            if move.origin:
                                lines.append({'origin': move.origin, 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done,'out_qty': 0.0})
                            else: 
                                lines.append({'origin': move.reference, 'move_date': move_date, 'product_id': move.product_id,'in_qty':move.qty_done,'out_qty': 0.0})
                    
                    for move in self.env['stock.move.line'].search([('id','=',stock_move.id),('picking_type_id.code','=', 'outgoing'), '|',('move_id.warehouse_id', '=', self.warehouse_id.id), ('move_id.warehouse_id', '=', False)]):
                        if move:
                            move_date = move.date
                            if move.origin:
                                lines.append({'origin': move.origin, 'move_date': move_date,'out_qty': move.qty_done,'product_id':move.product_id,'in_qty':0.0})
                            else:
                                   lines.append({'origin': move.reference, 'move_date': move_date,'out_qty': move.qty_done,'product_id':move.product_id, 'in_qty':0.0})
                                    
            sorted_lines = sorted(lines, key=lambda x: x['move_date'], reverse=False)
            
            product = []
            for rec in sorted_lines:   
                product.append(rec['product_id'])
            line_row = line
            for product_id in set(product):
                if product_id:
                    worksheet.write_merge(line_row,line_row,0,4, product_id.display_name, style=xlwt.easyxf("font: name Liberation Sans, bold on;align: horiz centre; pattern: pattern solid, pattern_fore_colour light_blue;"))
                    line = line_row + 1
                    worksheet.write_merge(line, line, 0, 3, 'Opening Balance',style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                    worksheet.write(line, 4, '0', style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                    total_in_qty = 0.0
                    total_out_qty = 0.0
                    total_balance = 0.0
                    balance = 0.0
                    line = line + 1
                    for rec in sorted_lines:
                        if product_id.id == rec['product_id'].id:
                            worksheet.write(line, 0, rec['move_date'].strftime('%m-%d-%Y'), style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                            worksheet.write(line, 1, rec['origin'], style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                            worksheet.write(line, 2, rec['in_qty'], style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                            worksheet.write(line, 3, rec['out_qty'], style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                            balance += rec['in_qty']
                            balance -= rec['out_qty']
                            worksheet.write(line, 4, balance, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center;"))
                            line += 1
                            total_in_qty += rec['in_qty']
                            total_out_qty += rec['out_qty']
                            total_balance = total_in_qty - total_out_qty
                    worksheet.write(line, 0, ' ', style=xlwt.easyxf("font: name Liberation Sans; align: horiz center; pattern: pattern solid, pattern_fore_colour gray50;"))
                    worksheet.write(line, 1, 'Total', style=xlwt.easyxf("font: name Liberation Sans; align: horiz center; pattern: pattern solid, pattern_fore_colour gray50;"))
                    worksheet.write(line, 2, total_in_qty, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center; pattern: pattern solid, pattern_fore_colour gray50;"))
                    worksheet.write(line, 3, total_out_qty, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center; pattern: pattern solid, pattern_fore_colour gray50;"))
                    worksheet.write(line, 4, total_balance, style=xlwt.easyxf("font: name Liberation Sans; align: horiz center; pattern: pattern solid, pattern_fore_colour gray50;"))
                line_row = line + 2

        fp = io.BytesIO()
        workbook.save(fp)

        export_id = self.env['excel.report'].create(
            {'excel_file': base64.encodebytes(fp.getvalue()), 'file_name': filename})
        res = {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'excel.report',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
        return res