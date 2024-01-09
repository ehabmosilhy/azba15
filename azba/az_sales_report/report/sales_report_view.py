# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
import operator
from datetime import datetime, date
from odoo.tools.float_utils import float_round


class SalesReportTemplate(models.AbstractModel):
    _name = 'report.az_sales_report.sales_report_template'
    _description = 'Stock Card Report Template'

    def get_product_detail(self, data):
        # Retrieve date range for filtering stock moves
        start_date_data = data.get('date_from')
        end_date_data = data.get('date_to')

        # Depending on the report type, construct the product IDs SQL
        product_ids = data.get('product_ids')
        product_ids_clause = ""
        params = [start_date_data, end_date_data]

        if product_ids:
            product_ids_clause = "AND aml.product_id IN %s"
            params.append(tuple(product_ids.ids))

        # Construct the SQL to fetch all relevant stock moves
        stock_move_sql = f"""
               SELECT
            aml.product_id,
            pt.code as code,
            pt.name as name,
            SUM(aml.quantity) as quantity,
            SUM(aml.price_total) as total_price_tax,
            SUM(aml.price_subtotal) as total_price_no_tax
        FROM account_move_line aml
        JOIN account_move am ON aml.move_id = am.id
        JOIN product_product pp ON aml.product_id = pp.id
        JOIN product_template pt ON pp.product_tmpl_id = pt.id
        WHERE am.invoice_date BETWEEN %s AND %s
        AND am.state = 'posted'
        {product_ids_clause}
        AND am.move_type IN ('out_invoice', 'out_refund')
        GROUP BY aml.product_id, pt.code, pt.name
        order by pt.code
        """
        self.env.cr.execute(stock_move_sql, tuple(params))
        stock_moves = self.env.cr.dictfetchall()

        return stock_moves

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        product_ids = self.env['product.product'].search([('product_tmpl_id', 'in', data['form']['product_tmpl_ids'])])

        data = {
            'date_from': date_from,
            'date_to': date_to,
            'product_ids': product_ids,
        }
        docargs = {
            'doc_model': 'az.sales.report',
            'data': data,
            'get_product_detail': self.get_product_detail,
        }
        return docargs
