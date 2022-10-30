# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockScrap(models.Model):
    _name = 'stock.scrap'
    _description = 'Stock Scrapp'
    _inherit = ['stock.scrap']
    _order = 'name'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('stocks_manger', 'Agreed By Stock Manger'),
        ('done', 'تمت موافقة المشرف على المشتريات والمستودعات')], string='Status', default="draft")

    def button_stocks_manger_validation(self):
        for record in self:
            record.state = 'stocks_manger'

    # @api.multi
    # def button_university_manger_validation(self):
    #     for record in self:
    #         record.state = 'university_manger'
