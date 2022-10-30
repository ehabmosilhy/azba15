# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EmployeeQualificationConfig(models.Model):
    _name = 'employee.qualification'
    _description = 'Employee Qualification'

    name = fields.Char('Name')


class EmployeeMajorConfig(models.Model):
    _name = 'employee.major'
    _description = 'Employee Major'

    name = fields.Char('Name')
