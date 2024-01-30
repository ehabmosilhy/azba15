# -*- coding: utf-8 -*-

from odoo import fields, models,api
from odoo.exceptions import  ValidationError

class ProductInOut(models.TransientModel):
    _name = "az.product.inout"


    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    source_location = fields.Many2one('stock.location', string="Source Location")
    destination_location = fields.Many2one('stock.location', string="Destination Location")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company
                                 , required=True)
    product_ids = fields.Many2many("product.product", string="Product")

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for record in self:
            if record.date_from and record.date_to:
                if record.date_to < record.date_from:
                    raise ValidationError("End date must be greater than start date!")

    def get_inout_report(self):
        [data] = self.read()
        datas = {
            'ids': [1],
            'model': 'az.product.inout',
            'form': data
        }
        action = self.env.ref('az_inventory.inout_report_action').report_action(self, data=datas)
        return action
