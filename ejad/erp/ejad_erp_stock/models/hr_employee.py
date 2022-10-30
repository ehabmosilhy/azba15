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

    employee_custody_count = fields.Integer( 'Custody count', compute='_compute_employee_custody_count')

    def action_get_custody_lines(self):
        action = self.env.ref('ejad_erp_hr.action_employee_custody_request').read([])[0]
        action['domain'] = [('employee_id', '=', self.id)]
        return action

    def _compute_employee_custody_count(self):
        for rec in self:
            employee_custody = self.env['employee.custody.request'].search(([('employee_id', '=', rec.id)]))
            rec.employee_custody_count = len(employee_custody)

