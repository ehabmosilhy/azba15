from odoo import fields, models


class HREmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'
    visa_issue_date = fields.Date()
    work_start_date = fields.Date()


