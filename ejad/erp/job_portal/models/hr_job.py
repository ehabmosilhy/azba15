# See LICENSE file for full copyright and licensing details.
from datetime import *
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrJobType(models.Model):
    _name = "hr.job.type"
    _description = "Job Type"

    name = fields.Char('Job Type')


class HrJob(models.Model):
    _inherit = 'hr.job'

    benefits_ids = fields.One2many('hr.job.benefits', 'job_benefits_id',
                                   string='Benefits')
    job_requirement_ids = fields.One2many('hr.job.requirement',
                                          'job_requirement_id',
                                          string='Requirements')
    job_by_area = fields.Char('Jobs by Functional Area')
    closing_date = fields.Date('Closing Date')
    notify_email = fields.Char('Application Notify Email')
    location_ids = fields.One2many('hr.job.location', 'job_location_id',
                                   string='Location')
    job_type_id = fields.Many2one('hr.job.type', string='Job Type')

    @api.constrains('closing_date')
    def validate_dates(self):
        if not self.env.context.get('website_id'):
            today = date.today()
            if self.closing_date:
                if today >= self.closing_date:
                    raise ValidationError("Closing date should be greater than"
                                          " Current Date.")


class HrJobBenefits(models.Model):
    _name = "hr.job.benefits"
    _description = "Job Benefits"

    name = fields.Char('Benefit')
    job_benefits_id = fields.Many2one('hr.job', string="Job")


class HrJobRequirement(models.Model):
    _name = "hr.job.requirement"
    _description = "Job Requirement"

    name = fields.Char('Requirement')
    job_requirement_id = fields.Many2one('hr.job', string="Job")


class HrJobLocation(models.Model):
    _name = "hr.job.location"
    _description = "Job Location"

    name = fields.Char('Location')
    job_location_id = fields.Many2one('hr.job', string="Job")
