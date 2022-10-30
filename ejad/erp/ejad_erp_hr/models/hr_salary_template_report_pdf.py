# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from pytz import timezone


class SalaryLetterTemplateReport(models.AbstractModel):
    _name = 'report.ejad_erp_hr.hr_salary_template_report_pdf'
    _description = 'Hr Salary Template Report pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        
        docargs = {
            'docs': self.env['hr.employee.salary.letter'].browse([data['form'][0]['id']]),
            'data': data['form'][0]
        }
        return docargs
