# -*- coding: utf-8 -*-

from odoo import models, api


class InoutReportTemplate(models.AbstractModel):
    _name = 'report.az_inventory.inout_report_template'
    _description = 'inout Report Template'

    def get_inout_details(self, data):
        # Retrieve date range for filtering account moves
        _product_ids= data.get('product_ids')
        product_ids = tuple(_product_ids) if len(_product_ids) > 0 else f'({_product_ids})'
        company_id = data.get('company_id')
        start_date = data.get('date_from')
        end_date = data.get('date_to')
        location= data.get('location')[0]

        q = f"""
        
            SELECT pt.code, pt.name,
        SUM(CASE WHEN (sml.location_dest_id = {location}  or sml.location_dest_id in (select id from stock_location where location_id={location})) AND sp.date < '{start_date}' THEN sml.qty_done ELSE 0 END) AS qty_in_before_start_date,
        SUM(CASE WHEN (sml.location_id = {location}  or sml.location_id in (select id from stock_location where location_id={location})) AND sp.date < '{start_date}' THEN sml.qty_done ELSE 0 END) AS qty_out_before_start_date,
        SUM(CASE WHEN (sml.location_dest_id = {location}  or sml.location_dest_id in (select id from stock_location where location_id={location})) AND sp.date >= '{start_date}' THEN sml.qty_done ELSE 0 END) AS qty_in,
        SUM(CASE WHEN (sml.location_id = {location} or sml.location_id in (select id from stock_location where location_id={location})) AND sp.date >= '{start_date}' THEN sml.qty_done ELSE 0 END) AS qty_out
            FROM
                stock_move_line sml
            JOIN
                stock_move sm ON sml.move_id = sm.id
            JOIN
                stock_picking sp ON sm.picking_id = sp.id
            JOIN
                stock_location sl_source ON sm.location_id = sl_source.id
            JOIN
                stock_location sl_destination ON sm.location_dest_id = sl_destination.id
            join product_product p on sml.product_id = p.id  
            join product_template pt on pt.id = p.product_tmpl_id
            WHERE
                sp.state = 'done'
                AND sp.company_id = {company_id}
                AND sml.product_id in {product_ids}
                AND sp.date <= '{end_date}'
                group by pt.code, pt.name
                order by pt.code;
        """
        self.env.cr.execute(q)
        product_inout_records = self.env.cr.dictfetchall()
        return product_inout_records

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        company_id = data['form']['company_id'][0]
        product_ids = data['form']['product_ids']
        location = data['form']['location']

        data = {
            'date_from': date_from,
            'date_to': date_to,
            'company_id': company_id,
            'product_ids': product_ids,
            'location': location,
        }
        docargs = {
            'doc_model': 'az.product.inout',
            'data': data,
            'get_inout_details': self.get_inout_details,
        }
        return docargs
