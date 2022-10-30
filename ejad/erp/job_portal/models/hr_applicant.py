# See LICENSE file for full copyright and licensing details.
from datetime import *
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.translate import _


class HrApplicant(models.Model):
    _inherit = 'hr.applicant'

    middlename = fields.Char('اسم الاب')
    lastname = fields.Char('اسم الجد')
    english_name = fields.Char('English Name')
    familyname = fields.Char('لقب العائلة')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
                              string="نوع الجنس")
    birthday = fields.Date('تاريخ الميلاد')
    IdEndDate = fields.Date(' تاريخ انتهاء الهوية')

    place_of_birth = fields.Char('Place of Birth')
    country_of_birth_lt = fields.Many2one('res.country')
    marital = fields.Selection(
        [('single', 'Single'),
         ('married', 'Married'),
         ('widower', 'Widower'),
         ('divorced', 'Divorced')],
        'Marital Status')
    #   Citizenship & Other Info
    identification_id = fields.Char('رقم الهوية')

    passport_id = fields.Char('رقم الجواز')
    country_id = fields.Many2one('res.country')
    provident_fund_id = fields.Char('Provident Fund No')
    #   Permanent Address
    is_same_address = fields.Boolean('Same as Correspondence Address')
    street_ht = fields.Char('شارع')
    street2_ht = fields.Char('شارع 2')
    city_ht = fields.Char('المدينة')
    zip_ht = fields.Char('الرمز البريدي')
    state_id_ht = fields.Many2one('res.country.state', string="المحافظة")
    #   Contact Address
    street_ca = fields.Char('شارع')
    street2_ca = fields.Char('شارع 2')
    city_ca = fields.Char('المدينة')
    zip_ca = fields.Char('الرمز البريدي')
    state_id_ca = fields.Many2one('res.country.state', string="الولاية او المحافظه")

    #   Job reference
    ref_name = fields.Char('Referred by')
    ref_org = fields.Char('Organization')
    ref_rel = fields.Char('Relation')
    ref_contact = fields.Char('Contact Details')

    arabic_level = fields.Selection(
        [('Beginner','مبتدىء'),('Midlevel','متوسط'),('Expert','خبير')]
        ,string="مستوى اللغة العربية")
    english_level = fields.Selection(
        [('Beginner', 'مبتدىء'), ('Midlevel', 'متوسط'), ('Expert', 'خبير')]
        , string="مستوى اللغة العربية")

    #   academic, experience, certifications histories
    academic_ids = fields.One2many('hr.academic', 'applicant_id',
                                   'Academic experiences',
                                   help="Academic experiences")
    experience_ids = fields.One2many('hr.experience', 'applicant_id',
                                     'Professional Experiences',
                                     help='Define Professional Experiences')
    certification_ids = fields.One2many('hr.mewan_skills', 'applicant_id',
                                        'Skills',
                                        help="المهارات")
    skills_ids = fields.One2many('hr.mewan_skills', 'applicant_id',
                                 'المهارات',
                                 help="المهارات الخاصة بالموظف")

    is_hr = fields.Boolean(compute="_check_user_group")

    @api.depends('job_id')
    def _check_user_group(self):
        self.is_hr = self.env.user.has_group('hr_recruitment.group_hr_recruitment_manager')



    @api.constrains('salary_expected', 'salary_proposed', 'birthday')
    def validate_applicants(self):
        if not self.env.context.get('website_id'):
            if self.salary_expected and self.salary_expected < 0:
                raise ValidationError("Please enter expected salary properly!")
            if self.salary_proposed and self.salary_proposed < 0:
                raise ValidationError("Please enter proposed salary properly!")
            if self.birthday:
                today = date.today()
                if today <= self.birthday:
                    raise ValidationError("Please enter birth date properly!")

    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(
                    ['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            else:
                new_partner_id = self.env['res.partner'].create({
                    'is_company': False,
                    'name': applicant.partner_name,
                    'email': applicant.email_from,
                    'phone': applicant.partner_phone,
                    'mobile': applicant.partner_mobile,
                    'country_id': applicant.country_id.id,
                })
                address_id = new_partner_id.address_get(['contact'])['contact']
            if applicant.job_id and (applicant.partner_name or contact_name):
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                employee = self.env['hr.employee'].create({
                    'birthday': applicant.birthday,
                    'gender': applicant.gender,
                    'marital': applicant.marital,
                    'zip_ht': applicant.zip_ht,
                    'state_id_ht': applicant.state_id_ht.id,
                    'country_id': applicant.country_id.id,
                    'city_ht': applicant.city_ht,
                    'mobile_phone': applicant.partner_mobile,
                    'street_ht': applicant.street_ht,
                    'street2_ht': applicant.street2_ht,
                    'identification_id': applicant.identification_id,
                    'name': applicant.partner_name or contact_name,
                    'job_id': applicant.job_id.id,
                    'address_home_id': address_id,
                    'work_email': applicant.email_from,
                    'passport_id': applicant.passport_id,
                    'work_phone': applicant.partner_phone,
                    'place_of_birth': applicant.place_of_birth,
                    'country_of_birth': applicant.country_of_birth_lt.id,
                    'department_id': applicant.department_id.id or False,
                    'address_id': applicant.company_id
                    and applicant.company_id.partner_id
                    and applicant.company_id.partner_id.id or False,
                })
                applicant.write({'emp_id': employee.id})
                applicant.job_id.message_post(
                    body=_('New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
            else:
                raise UserError(_('You must define an Applied Job and a Contact Name for this applicant.'))
        for acad in applicant.academic_ids:
            self.env['hr.academic'].create({
                'name': acad.name,
                'employee_id': employee.id,
                'organization': acad.organization,
                'study_field': acad.study_field,
                'location': acad.location,
                'start_date': acad.start_date,
                'end_date': acad.end_date,
                'is_still': acad.is_still,
                'grade': acad.grade,
                'activities': acad.activities,
                'description': acad.description
            })
        for certificate in applicant.certification_ids:
            self.env['hr.certification'].create({
                'name': certificate.name,
                'employee_id': employee.id,
                'certification': certificate.certification,
                'organization': certificate.organization,
                'location': certificate.location,
                'start_date': certificate.start_date,
                'end_date': certificate.end_date,
                'is_still': certificate.is_still,
                'description': certificate.description
            })
        for experience in applicant.experience_ids:
            self.env['hr.experience'].create({
                'name': experience.name,
                'employee_id': employee.id,
                'type': experience.type,
                'organization': experience.organization,
                'location': experience.location,
                'start_date': experience.start_date,
                'end_date': experience.end_date,
                'is_still': experience.is_still,
                'description': experience.description,
                'referee_name': experience.referee_name,
                'referee_position': experience.referee_position,

            })
        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        if employee:
            dict_act_window['res_id'] = employee.id
        dict_act_window['view_mode'] = 'form,tree'
        return dict_act_window
