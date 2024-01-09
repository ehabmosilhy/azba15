# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import  ValidationError

class SalesReport(models.TransientModel):
    _name = "az.sales.report"
    _description = "Sales Report"

    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    product_tmpl_ids = fields.Many2many('product.template',string="Product")

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_to < record.date_from:
                    raise ValidationError("End date must be greater than start date!")

    def get_sales_report(self):
        [data] = self.read()
        datas = {
             'ids': [1],
             'model': 'az.sales.report',
             'form': data
        }
        action = self.env.ref('az_sales_report.sales_report_action_view').report_action(self, data=datas)
        return action
