# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime

from odoo import api, fields, models
from odoo.tools.float_utils import float_round


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    current_leave_state = fields.Selection(compute='_compute_leave_status', string="Current Time Off Status",
                                           selection=[
                                               ('draft', 'الموظف'),
                                               ('cancel', 'Cancelled'),
                                               ('direct_manager', 'المدير المباشر'),
                                               ('hr_approve', 'مسؤول الموارد البشرية'),
                                               ('confirm', 'مدير إدارة الخدمات المساندة'),
                                               ('validate1', 'قائد المكتب'),
                                               ('validate', 'تم الموافقة'),
                                               ('refuse', 'تم الرفض'),

                                           ])
