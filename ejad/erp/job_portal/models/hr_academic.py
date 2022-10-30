# See LICENSE file for full copyright and licensing details.
from datetime import *
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrAcademic(models.Model):
    _name = 'hr.academic'
    _inherit = 'hr.curriculum'
    _description = 'Academic experiences'

    inistitue = fields.Many2one('hr.institute',string="الجهة التعليمية")
    country_id = fields.Many2one('res.country',string="الدولة")
    state_id = fields.Many2one('res.country.state', string="المدينة")
    study_field = fields.Many2one('hr.specializations',string="التخصص")
    qualification = fields.Selection(
        [('BA','بكالوريوس'),
         ('MA','ماجستير'),
         ('PH','دكتوراه'),
         ('DIP','دبلوم')],
    string="الدرجة العلمية")

    activities = fields.Text(string='Activities and associations',
                             translate=True)

    @api.constrains('start_date', 'end_date')
    def validate_dates(self):
        if not self.env.context.get('website_id'):
            if self.end_date:
                today = date.today()
                for dates in self:
                    if dates.start_date > today:
                        raise ValidationError(_('Start date (%s) should be less than Current Date in Academic Experience') % dates.start_date)
                    if dates.end_date > today:
                        raise ValidationError(_('End date (%s) should be less than Current Date in Academic Experience') % dates.end_date)
                    if dates.start_date > dates.end_date:
                        raise ValidationError(_('End date (%s) should be greater than Start Date (%s) in Academic Experience') % dates.start_date, dates.end_date)

    def write(self, vals):
        if vals.get("is_still"):
            vals.update({'end_date': None})
        result = super(HrAcademic, self).write(vals)
        return result




class HrInstitute(models.Model):
    _name = "hr.institute"
    _description = "Hr Institute"

    name = fields.Char("المعاهد والجامعات")
    country_id = fields.Many2one("res.country", "الدولة")
    state_id = fields.Many2one("res.country.state", "المدينة")



class SPECIALIZATIONS(models.Model):
    _name = "hr.specializations"
    _description = "Academic Specializations"

    name = fields.Char()

class CompanySectors(models.Model):
    _name = "hr.sectors"
    _description = "Companies Sectors"

    name = fields.Char()


class SKILLS(models.Model):
    _name = "hr.mewan_skills"
    _description = "Personal Skills"

    name = fields.Char(string="وصف المهارة")
    skill_level = fields.Selection(
        [('Beginner','مبتدىء'),('MidLevel','متوسط'),('Expert','خبير')]
        ,string="مستوى المهارة")
    partner_id = fields.Many2one('res.partner')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    applicant_id = fields.Many2one('hr.applicant', string='Application')
    partner_id = fields.Many2one('res.partner', string='Partner')