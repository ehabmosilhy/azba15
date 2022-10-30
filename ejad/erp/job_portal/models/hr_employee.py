# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    #   Personal details
    middlename = fields.Char("Name")
    lastname = fields.Char("Name")
    country_of_birth_lt = fields.Many2one('res.country')
    #   Permanent Address
    is_same_address = fields.Boolean("Same as Correspondence Address")
    street_ht = fields.Char("Street")
    street2_ht = fields.Char("Street2")
    city_ht = fields.Char("City")
    state_id_ht = fields.Many2one('res.country.state', string="State")
    zip_ht = fields.Char("Zip")
    #   Previous Employment Verification
    ref_name = fields.Char("Referred by")
    ref_org = fields.Char("Organization")
    ref_rel = fields.Char("Relation")
    ref_contact = fields.Char("Contact details")
    #   family details
    fam_spouse = fields.Char("Name")
    fam_spouse_employer = fields.Char("Employer")
    fam_spouse_tel = fields.Char("Telephone.")
    fam_father = fields.Char("Father's Name")
    fam_father_date_of_birth = fields.Date("Date of Birth")
    fam_mother = fields.Char("Mother's Name")
    fam_mother_date_of_birth = fields.Date("Date of Birth")
    #   academic, experience, certifications, family histories
    academic_ids = fields.One2many('hr.academic', 'employee_id',
                                   'Academic experiences',
                                   help="Academic experiences")
    experience_ids = fields.One2many('hr.experience', 'employee_id',
                                     ' Professional Experiences',
                                     help='Professional Experiences')
    certification_ids = fields.One2many('hr.certification', 'employee_id',
                                        'Certifications',
                                        help="Certifications")
    skills_ids = fields.One2many('hr.mewan_skills', 'employee_id',
                                 'المهارات',
                                 help="المهارات الخاصة بالموظف")
    fam_children_ids = fields.One2many('hr.employee.children', 'employee_id',
                                       "Children")

    operation_type = fields.Char()
    opr_id = fields.Char()
