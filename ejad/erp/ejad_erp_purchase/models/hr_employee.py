# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HREmployee(models.Model):
    _name = 'hr.employee'
    _description = 'HR Employee'
    _inherit = ['hr.employee']
    _order = 'name'

    employee_requset_count = fields.Integer( 'Product Requset count', compute='_compute_employee_requsest_count')

    def action_get_request_lines(self):
        action = self.env.ref('ejad_erp_purchase.action_employee_products_request').read([])[0]
        action['domain'] = [('employee_id', '=', self.id)]
        return action

    def _compute_employee_requsest_count(self):
        for rec in self:
            employee_requset_count = self.env['purchase.requisition.request'].search(([('employee_id', '=', rec.id)]))
            rec.employee_requset_count = len(employee_requset_count)

