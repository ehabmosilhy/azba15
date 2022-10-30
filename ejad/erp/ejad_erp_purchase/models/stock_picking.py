# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking']


    def action_cancel(self):
        if self.requisition_request_id:
            self.requisition_request_id.state = 'canceled'
        return super(StockPicking, self).action_cancel()