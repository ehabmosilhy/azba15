# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockInventory(models.Model):
    _name = 'stock.inventory'
    _description = 'Stock Picking'
    _inherit = ['stock.inventory']
    _order = 'name'

    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'In Progress'),
        ('stocks_manger', 'Agreed By Stock Manger'),
        ('done', 'اعتماد المشرف على المشتريات والمستودعات')],
                             copy=False, index=True, readonly=True,
                             default='draft')

    def button_stocks_manger_validation(self):
        for record in self:
            record.state = 'stocks_manger'

    # @api.multi
    # def button_university_manger_validation(self):
    #     for record in self:
    #         record.state = 'done'

