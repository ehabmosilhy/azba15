from odoo import fields, models


class HREmployee(models.AbstractModel):
    _inherit = 'hr.employee.base'
    visa_issue_date = fields.Date()
    work_start_date = fields.Date()
    medical_certificate_number = fields.Char()
    medical_certificate_number_issue_date = fields.Date()
    medical_certificate_number_expiration_date = fields.Date()
