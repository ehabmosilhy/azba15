from odoo import fields, models


class HREmployee(models.Model):
    _inherit = 'hr.employee'
    visa_issue_date = fields.Date()
    work_start_date = fields.Date()
