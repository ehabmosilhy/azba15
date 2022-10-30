# See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class HrCurriculum(models.Model):
    _name = 'hr.curriculum'
    _description = "Employee's Curriculum"

    name = fields.Char('Name', required=True)
    start_date = fields.Date('Start date')
    is_still = fields.Boolean()
    end_date = fields.Date('End date')
    grade = fields.Char('Grade')
    organization = fields.Char('Organization',
                               help="Employer, School, University, "
                                    "Organization, Institution, Company, "
                                    "Certification "
                                    "Authority")
    location = fields.Char('Location', help="Location")
    description = fields.Text('Description')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    applicant_id = fields.Many2one('hr.applicant', string='Application')
    partner_id = fields.Many2one('res.partner', string='Partner')
    state_id = fields.Many2one('res.country.state', string="المدينة")
    country_id = fields.Many2one('res.country')