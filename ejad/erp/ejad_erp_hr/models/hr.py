# -*- coding: utf-8 -*-
# Copyright YEAR(S), AUTHOR(S)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import time
from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from lxml import etree
# from odoo.osv.orm import setup_modifiers


import re, logging
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

def convert_date_to_dayinweek(date):
    formatted_date = datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
    day_in_week = formatted_date.strftime("%A")
    return day_in_week


# class ResUsers(models.Model):
#
#     _inherit = 'res.users'
#
#     @api.model
#     def create(self, vals):
#         res = super(ResUsers, self).create(vals)
#         # res.workflow_init()
#         if vals.get('login', False):
#             emp_ids = self.env['hr.employee'].search([('work_email', '=', (vals.get('login', False)).lower())])
#             if emp_ids:
#                 emp_ids.user_id = res.id
#         return res


class Department(models.Model):
    _inherit = "hr.department"
    _description = "HR Department"

    types = fields.Selection([('PUN', ' Presidency University'),
                              ('DOUN', 'Deanship of University'),
                              ('admin', 'Administration'),
                              ('Agency', 'Agency'),
                              ('center', 'Center'),
                              ('Department', 'Department')], string="Type OF Department")


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'


    @api.constrains('acc_number', 'account_type')
    def _check_bank_account_number(self):
        if (self.acc_number) and (self.account_type == 'internal'):
            if len(self.acc_number) != 24:
                raise UserError(_("Please Check the Bank Account Number"))
            elif str(self.acc_number)[0:2] != 'SA':
                raise UserError(_("Please Check the Bank Account Number"))
            #elif not str(self.acc_number)[2:].isdigit():
            #    raise UserError(_("Please Check the Bank Account Number"))


    @api.depends('acc_number', 'account_type')
    def _compute_has_char(self):
        if (self.acc_number) and (self.account_type == 'internal'):
            if not str(self.acc_number)[2:].isdigit():
                self.has_char = True
            else:
                self.has_char = False
        else:
            self.has_char = False

    has_char = fields.Boolean(compute='_compute_has_char', string="رقم الحساب المحلي يحتوي على حروف", store=True, )
    account_type = fields.Selection(
        [('internal', 'محلي'), ('external', 'دولي')], string="نوع الحساب", default="internal"
    )
    additional_info = fields.Html('معلومات أخرى')


class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = ['hr.employee']

    def print_salary_letter(self):
        # print(self.env.context)
        for rec in self:
            c_ids = rec.env['hr.contract'].search([('employee_id', '=', rec.env.context.get('emp', False))])
            action = rec.env.ref('ejad_erp_hr.hr_employee_salary_letter_action')
            action_data = action.read()[0]
            action_data.update({
                'context': {
                    'default_contract_id': c_ids and c_ids[0].id or False,
                }
            })
            return action_data
    #
    # def read(self, fields=None, load='_classic_read'):
    #     # if self.env.context.get('params', False):
    #         # if (self.env.context.get('params', False).get('employee_action', False) and ((self.env.context.get('params', False).get('view_type', False)) == 'form')) or self.env.context.get('employee_action', False):
    #         #     print("  111111  ", self.env.context)
    #         #     if not (self.env.context.get('params', False) and self.env.context.get('params', False).get('menu_id', False)):
    #         #         print("  YYEESSS  ", self.env.context)
    #     if self.env.context and self.env.context.get('params', False):
    #             if  '_push_me' in self.env.context.get('params', False):
    #                 for rec in self:
    #                     if rec.id != 1:
    #                         return {}
    #     results = super(HrEmployee, self).read(
    #         fields=fields, load=load)
    #     return results

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        if self.env.context.get('employee_action'):
            if self.env.user.has_group('ejad_erp_hr.access_all_employee'):
                domain += [('id', '!=', -1)]
            elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
                self._cr.execute("SELECT eemp.department_id as department_id,eemp.id as id FROM hr_employee eemp "
                                 "join resource_resource rr ON(rr.id=eemp.resource_id) WHERE rr.user_id= %d" % (
                                 self.env.user.id,))
                res = self.env.cr.dictfetchall()
                domain += ['|', ('parent_id', '=', res and res[0]['id'] or False), ('department_id', 'child_of', res and res[0]['department_id'] or [])]
            elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
                self._cr.execute("SELECT eemp.id as id FROM hr_employee eemp "
                                 "join resource_resource rr ON(rr.id=eemp.resource_id) WHERE rr.user_id= %d" %(self.env.user.id,))
                res = self.env.cr.dictfetchall()
                domain += ['|', ('parent_id', '=', res and res[0]['id'] or False), ('user_id', '=', self.env.user.id)]
            elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
                domain += [('user_id', '=', self.env.user.id)]
            else:
                domain += [('id', '=', -1)]
        res = super(HrEmployee, self).search(domain, offset=offset, limit=limit, order=order, count=count)
        return res

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.context.get('employee_action'):
            if self.env.user.has_group('ejad_erp_hr.access_all_employee'):
                domain += [('id', '!=', -1)]
            elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
                self._cr.execute("SELECT eemp.department_id as department_id,eemp.id as id FROM hr_employee eemp "
                                 "join resource_resource rr ON(rr.id=eemp.resource_id) WHERE rr.user_id= %d" % (
                                 self.env.user.id,))
                res = self.env.cr.dictfetchall()
                domain += ['|', ('parent_id', '=', res and res[0]['id'] or False), ('department_id', 'child_of', res and res[0]['department_id'] or [])]
            elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
                self._cr.execute("SELECT eemp.id as id FROM hr_employee eemp "
                                 "join resource_resource rr ON(rr.id=eemp.resource_id) WHERE rr.user_id= %d" %(self.env.user.id,))
                res = self.env.cr.dictfetchall()
                domain += ['|', ('parent_id', '=', res and res[0]['id'] or False), ('user_id', '=', self.env.user.id)]
            elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
                domain += [('user_id', '=', self.env.user.id)]
            else:
                domain += [('id', '=', -1)]
        res = super(HrEmployee, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res

    # @api.onchange('user_id')
    # def _onchange_user(self):
    #     a = False

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10000):
        args = args or []
        domain = []
        if name and name.isdigit():
            domain = ['|', '|', '|', ('work_email', 'ilike', name), ('en_name', 'ilike', name), ('name', 'ilike', name), ('emp_attendance_no', '=', int(name))]
        elif name:
            domain = ['|', '|', ('work_email', 'ilike', name), ('en_name', 'ilike', name), ('name', 'ilike', name)]
        emp = self.search(domain + args, limit=limit)
        return emp.name_get()



    @api.constrains('work_email', 'bank_account_id')
    def _check_employee_email_bank_account_number(self):
        if (self.work_email) and (re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$',
                                           self.work_email) == None):
            raise UserError(_("Please Check the email Syntax"))
        if (self.bank_account_id.acc_number) and (self.bank_account_id.account_type == 'internal'):
            if len(self.bank_account_id.acc_number) != 24:
                raise UserError(_("Please Check the Bank Account Number"))
            elif str(self.bank_account_id.acc_number)[0:2] != 'SA':
                raise UserError(_("Please Check the Bank Account Number"))
            elif not str(self.bank_account_id.acc_number)[2:].isdigit():
                raise UserError(_("Please Check the Bank Account Number"))

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(HrEmployee, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])
        if not self.env.user.has_group('ejad_erp_hr.access_join_upgrade_date_create'):
            for field in result['fields']:
                for node in doc.xpath("//field[@name='date_of_join']"):
                    node.set('readonly', '1')
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers["readonly"] = True
                    node.set("modifiers", json.dumps(modifiers))
                for node in doc.xpath("//field[@name='date_grade_update']"):
                    node.set('readonly', '1')
                    modifiers = json.loads(node.get("modifiers"))
                    modifiers["readonly"] = True
                    node.set("modifiers", json.dumps(modifiers))
        if view_type != 'search' and not self.env.user.has_group('ejad_erp_hr.access_employee_edit_create'):
            # root = etree.fromstring(result['arch'])
            doc.set('create', 'false')
            doc.set('edit', 'false')
            doc.set('delete', 'false')
            # print('5555555555  ')
            # result['arch'] = etree.tostring(root)
        result['arch'] = etree.tostring(doc)
        return result

    # Grade info
    # grade_type=fields.Selection([('SA','Scientific Authority'),('AD','Administration'),('SP','Specialization'),('PR','Profitable'),('OTHER','Other')],string=" Grade Type")
    def action_get_request_mandates(self):
        action = self.env.ref('ejad_erp_hr.action_employee_mandate_request').read([])[0]
        action['domain'] = [('employee_id', '=', self.id)]
        return action

    def _compute_employee_mandate_count(self):
        for rec in self:
            employee_mandate_count = self.env['hr.mandate.request'].search(([('employee_id', '=', rec.id)]))
            rec.employee_mandate_count = len(employee_mandate_count)

    bank_account_id = fields.Many2one(domain="[('id', '!=', -1)]")
    department_id2 = fields.Many2one('hr.department', string='Assignment Department')
    en_name = fields.Char(string="English Name")
    employee_mandate_count = fields.Integer('Mandate Requset count', compute='_compute_employee_mandate_count')
    grade_level_id = fields.Many2one(comodel_name='hr.grade.level', related="contract_id.grade_level_id",
                                     string="Grade/Level", store=True)
    grade_id = fields.Many2one('hr.grade', 'Grade', related="grade_level_id.grade_id", store=True)
    grade_type_id = fields.Many2one('hr.grade.type', 'Grade Type', related="grade_level_id.grade_type_id", store=True)

    # other info
    emp_type = fields.Selection([('basic', 'Basic'),
                                 ('Collaborative', 'Collaborative'),
                                 ('Retired', 'Retired')], string="Type OF Employee")
    contract_type = fields.Selection([('management', 'ادارين'),
                                      ('staff', 'مهنين')], string="نوع العقد")
    # contract_type = fields.Selection([('sicetific', 'هيئة علمية '),
    #                                   ('management', 'ادارين'),
    #                                   ('staff', 'مهنين')], string="نوع العقد")
    # address_home_id
    private_phone = fields.Char('Private Phone')
    private_email = fields.Char('Private Email')

    date_of_join = fields.Date(string='Join Date', required=True, default=fields.Date.context_today)
    date_grade_update = fields.Date(string='Last Grade Update')
    wage_incr_count = fields.Integer(string='Payroll Wage History', compute='_compute_incr_count')
    loans_count = fields.Integer(string='عدد القروض السابقة')
    payment_type = fields.Selection([('bank', 'Bank'), ('cash', 'Cash')], string="Payment Type")

    ens_months = fields.Integer(
        string='اشهر نهاية الخدمة',
        readonly=True,
        compute='_compute_ens_months'
    )
    has_gosi = fields.Boolean('هل له تأمين إجتماعي؟')
    has_saned = fields.Boolean('هل له ساند؟')
    qualification = fields.Many2one('employee.qualification', string='Qualification')
    major = fields.Many2one('employee.major', string='Major')
    graduation_year = fields.Char('Graduation Year')
    secondment_date = fields.Date(string="Secondment Date")
    contract_date = fields.Date(string="Contract Date")
    cooperation_date = fields.Date(string="Cooperation Date")
    hiring_date = fields.Date(string="Hiring Date")
    attachment_ids = fields.One2many(comodel_name="hr.employee.attachments", inverse_name="employee_id",
                                     string="المرفقات")

    @api.constrains('graduation_year')
    def _check_graduation_year(self):
        for record in self:
                if record.graduation_year and not record.graduation_year.isdigit() :
                    raise ValidationError(_('حقل سنة التخرج يجب أن يحتوي على أرقام فقط'))

    @api.depends('date_of_join')
    def _compute_ens_months(self):
        for record in self:
            ens_months = year = join_year = 0
            if record.date_of_join:
                join_year = datetime.strptime(str(record.date_of_join), '%Y-%m-%d').strftime('%Y')

                year = relativedelta(fields.Date.from_string(fields.Date.today()),
                                     fields.Date.from_string(record.date_of_join)).years
                if join_year <= '1999':
                    ens_months = year * 2
                else:
                    ens_months = year

            record.ens_months = ens_months

    def _compute_incr_count(self):
        for x in self:
            tpw_history = self.env['hr.payroll.wage.history']
            x.wage_incr_count = tpw_history.search_count(
                [('employee_id', '=', x.id),
                 ('difference', '>', 0)])


class HrContract(models.Model):
    _inherit = 'hr.contract'

    _sql_constraints = [
        ('employee_contract_uniq', 'unique(employee_id)', "يجب أن يكون هنالك عقد واحد فقط للموظف")
    ]

    def open_wizard(self):
        for rec in self:
            c_ids = rec.search([('name', '=', rec.env.context.get('contract_name', False))])
            action = rec.env.ref('ejad_erp_hr.hr_employee_salary_letter_action')
            action_data = action.read()[0]
            action_data.update({
                'context': {
                    'default_contract_id': c_ids and c_ids[0].id or False,
                }
            })
            return action_data

    @api.onchange('contract_type')
    def _onchange_contract_type(self):
        self.grade_type_id = False
        self.grade_level_id = False

    @api.onchange('grade_type_id')
    def _onchange_grade_type_id(self):
        self.grade_level_id = False

    @api.onchange('has_housing_allow', 'wage')
    def _onchange_house_allow(self):
        if self.has_housing_allow:
            housing_allow = self.wage * 3 / 12

            if housing_allow > 2000:
                housing_allow = 2000
            elif 1000 > housing_allow > 0:
                housing_allow = 1000
            self.hosing_allowancme = housing_allow
        else:
            self.hosing_allowancme = 0.0

    #
    @api.onchange('grade_level_id')
    # @api.depends('grade_level_id')
    def _onchange_grade_level_id(self):
        if self.grade_level_id:
            self.wage = self.grade_level_id.gross
            self.transfer_allowance = self.grade_level_id.transfer_allowance
            self.assignment_allowance = self.grade_level_id.assignment_allowance
            self.annual_allowance = self.grade_level_id.annual_allowance
            self.employee_id.grade_level_id = self.grade_level_id.id
            # self.other_allowance=self.grade_level_id.other_allowance
            # self.hosing_allowancme = self._onchange_house_allow1(self.has_housing_allow, self.wage or 0.0)

        else:
            self.wage = 0.0
            self.transfer_allowance = 0.0
            self.assignment_allowance = 0.0
            self.annual_allowance = 0.0
            # self.other_allowance= 0.0


    @api.depends('wage', 'other_allowancme', 'excp_wage', 'excp_housing', 'excp_transportation', 'excp_others',
                 'is_exceptional', 'grade_level_id', 'job_id', 'grade_level_id.transfer_allowance', 'employee_id',
                 'employee_id.job_id', 'has_housing_allow', 'hosing_allowancme')
    def get_total_gross_salary(self):
        for rec in self:
            if not rec.is_exceptional:
                wage = rec.wage or 0.00
                hosing_allowancme = 0.00
                # print('#########    ',wage)
                if rec.has_housing_allow:
                    hosing_allowancme = rec.hosing_allowancme or 0.00
                transfer_allowance = rec.grade_level_id.transfer_allowance or 0.00
                rec_job = rec.employee_id.job_id
                total = (rec_job.reward_dean_of_college_center or 0.00) + (
                            rec_job.reward_deputy_college_center or 0.00) + (
                                    rec_job.reward_admin_college_center or 0.00) + (
                                    rec_job.reward_manager_college or 0.00) + (
                                    (rec_job.reward_security_department or 0.00) * (wage / 100.00)) + (
                                (rec_job.reward_reception_department or 0.00) * (wage / 100.00)) + (
                                    (rec_job.reward_financial_department or 0.00) * (wage / 100.00)) + (
                                    rec_job.reward_government_relation or 0.00) + (rec_job.reward_calling or 0.00) + (
                                    rec_job.reward_passport_representative_external or 0.00) + (
                                    rec_job.reward_passport_representative_internal or 0.00) + (
                                rec_job.reward_purchase_representative or 0.00) + (
                                    rec_job.reward_revenue_collector or 0.00) + (rec_job.other_reward or 0.00) + (
                                    rec_job.food_reward or 0.00)
                total = total + wage + hosing_allowancme + transfer_allowance + (rec.other_allowancme or 0.00)
                rec.gross_salary = total
            else:
                rec.gross_salary = (rec.excp_wage or 0.00) + (rec.excp_housing or 0.00) + (
                            rec.excp_transportation or 0.00) + (rec.excp_others or 0.00)


    @api.onchange('is_exceptional')
    def onchange_is_exceptional(self):
        for rec in self:
            if rec.is_exceptional:
                rec.grade_level_id = False
                rec.grade_type_id = False
                rec.has_housing_allow = False
                rec.hosing_allowancme = 0.00
                rec.other_allowancme = 0.00
                rec.wage = 0.00

    employee_id = fields.Many2one(required=True)
    emp_attendance_no = fields.Integer(related='employee_id.emp_attendance_no', store=True)
    job_id = fields.Many2one('hr.job', related='employee_id.job_id', store=True)
    department_id = fields.Many2one('hr.department', related='employee_id.department_id', store=True)
    is_exceptional = fields.Boolean("Is Exceptional")
    is_exceptional_insurance = fields.Boolean("تأمين اجتماعي استثنائي")
    excp_wage = fields.Float(string='Exceptional Wage', default=0.00)
    excp_housing = fields.Float(string='Exceptional Housing', default=0.00)
    excp_transportation = fields.Float(string='Exceptional Transportation', default=0.00)
    excp_others = fields.Float(string='Exceptional Other Allowances', default=0.00)
    insurance_amount = fields.Float(string='المبلغ الخاضع للتأمين', default=0.00)
    gross_salary = fields.Float(string='Gross Salary', store=False, compute='get_total_gross_salary')
    name = fields.Char('Contract Reference', required=False, readonly=True, copy=False, default='/')
    grade_level_id = fields.Many2one(comodel_name='hr.grade.level', string="Grade/Level")
    grade_id = fields.Many2one('hr.grade', 'Grade id', related="grade_level_id.grade_id")
    has_housing_allow = fields.Boolean('هل له بدل سكن؟')
    grade_type_id = fields.Many2one('hr.grade.type', 'Grade Type')
    contract_type = fields.Selection([('sicetific', 'هيئة علمية '),
                                      ('management', 'ادارين'),
                                      ('staff', 'مهنين')], related="employee_id.contract_type", string="نوع العقد")

    transfer_allowance = fields.Float(string="Transfer allowance", related="grade_level_id.transfer_allowance")
    assignment_allowance = fields.Float(string="Assignment allowance", related="grade_level_id.assignment_allowance")
    annual_allowance = fields.Float(string="Annual Allowance", related="grade_level_id.annual_allowance")
    wage = fields.Float(string="Basic Salary", related="grade_level_id.gross")
    other_allowancme = fields.Float(string="other Allowance")
    special_allowance = fields.Float(string="special allowance")
    hosing_allowancme = fields.Float('بدل السكن')


    state = fields.Selection([
        ('draft', 'أخصائي الموارد البشرية'),
        ('support_services_manager', 'مدير إدارة الخدمات المساندة'),
        ('office_leader', 'قائد المكتب'),
        ('open', 'Running'),
        ('close', 'Expired'),
        ('cancel', 'Cancelled')
    ], string='Status', group_expand='_expand_states', copy=False,
        tracking=True, help='Status of the contract', default='draft')

    def action_support_services_manager(self):
        for rec in self:
            rec.write({'state': 'support_services_manager'})

    def action_office_leader(self):
        for rec in self:
            rec.write({'state': 'office_leader'})

    def action_open(self):
        for rec in self:
            rec.write({'state': 'open'})

    @api.model
    def create(self, vals):
        """
            Create Contract then create Wage History
            Passing Id of the Many2one fields to retrieve its name
            Write value of Many2one using format {'field_id':id}
        """
        if vals.get('number', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('contract.ref')
        cur_contract = super(HrContract, self).create(vals)
        new_vals = {'name': 'Wage History',
                    'employee_id': cur_contract.employee_id.id,
                    'department_id': cur_contract.department_id.id,
                    'contract_id': cur_contract.id,
                    'job_id': cur_contract.job_id.id,
                    'responsible_id': self.env.user.id,
                    'pre_wage': 0,
                    'cur_wage': cur_contract.wage,
                    'cur_grade_level_id': cur_contract.grade_level_id.id,

                    'effective_date': fields.Date.today(),
                    }
        self.env['hr.payroll.wage.history'].create(new_vals)
        return cur_contract


    def write(self, vals):
        """
            Update Contract -> Update Wage history with the current employee,
            1. Search for the newest Wage History on that Employee,
            2. Change and Update
        """
        for contract in self:
            if 'wage' in vals:

                new_vals = {'name': 'Promotion',
                            'employee_id': contract.employee_id.id,
                            'department_id': contract.department_id.id,
                            'contract_id': contract.id,
                            'job_id': contract.job_id.id,
                            'responsible_id': self.env.user.id,
                            'pre_wage': contract.wage,
                            'pre_grade_level_id': contract.grade_level_id.id,
                            'cur_grade_level_id': vals['grade_level_id'] or contract.grade_level_id.id,
                            # value of changed fields

                            'cur_wage': vals['wage'],
                            'effective_date': fields.Date.today(),
                            }
                self.env['hr.payroll.wage.history'].create(new_vals)
        return super(HrContract, self).write(vals)

    """
    Start workflow fields ( حقول المراحل )
    """
    category = fields.Many2one("dynamic.workflow.category", string="Category", tracking=True)

    # project_type = fields.Many2one("workflow.project.type", string="Project type", tracking=True, default=lambda self: self.env.ref('ejad_erp_hr.contract_project_type_data').id)
    # project_code = fields.Char(related="project_type.code")
    project_code = fields.Char()


    stage_ids = fields.Many2many("dynamic.workflow.stage", compute="_compute_stage_ids", tracking=True)
    # stage_id = fields.Many2one("dynamic.workflow.stage", string="المرحلة", tracking=True, default=lambda self: self.env.ref('ejad_erp_hr.dynamic_workflow_stage_data_0').id)
    stage_id = fields.Many2one("dynamic.workflow.stage")
    # , compute = "workflow_init" , default=_get_first_stage

    have_secondary_stage = fields.Boolean(
        string="have secondary stage", compute="check_current_stage_have_secondary_stage"
    )
    current_second_stage = fields.Many2one(
        "dynamic.workflow.stage", string="المرحلة الفرعية الحالية", tracking=True
    )
    secondary_stage_ids = fields.One2many(related="stage_id.secondary_stage_ids", string="Secondary stages")

    is_stage_success = fields.Boolean(related="stage_id.is_success_type")
    is_stage_refuse = fields.Boolean(related="stage_id.is_refuse_type")
    is_stage_first = fields.Boolean(related="stage_id.is_first_type")
    is_stage_cancel = fields.Boolean(related="stage_id.is_cancel_type")

    next_stage_permission = fields.Boolean("Next stage permission", compute="check_next_stage_permission")
    next_second_stage_permission = fields.Boolean("Next stage Second permission", compute="check_next_stage_permission")
    precedent_stage_permission = fields.Boolean(
        "Precedent stage permission", compute="check_precedent_stage_permission"
    )
    precedent_second_stage_permission = fields.Boolean(
        "Precedent stage Second permission", compute="check_precedent_stage_permission"
    )
    refuse_stage_permission = fields.Boolean("Refuse stage permission", compute="check_refuse_stage_permission")

    designation = fields.Boolean(related="stage_id.designation")
    designation_secondary_stage = fields.Boolean(related="current_second_stage.designation")

    designation_office = fields.Boolean(related="stage_id.designation_office")
    designation_office_secondary_stage = fields.Boolean(related="current_second_stage.designation_office")

    related_stages = fields.Char(
        compute="_compute_related_stages", help="Technical filed used for workflow stage display"
    )
    related_secondary_stages = fields.Char(
        compute="_compute_related_stages", help="Technical filed used for workflow stage display"
    )

    is_assign_employee_allowed = fields.Boolean(compute="_compute_is_assign_employee_allowed")
    is_assign_office_allowed = fields.Boolean(compute="_compute_is_assign_office_allowed")
    is_refuse_action_allowed = fields.Boolean(compute="_compute_is_refuse_action_allowed")
    is_return_action_allowed = fields.Boolean(compute="_compute_is_return_action_allowed")
    is_workflow_next_allowed = fields.Boolean(compute="_compute_is_workflow_next_allowed")
    is_workflow_previous_allowed = fields.Boolean(compute="_compute_is_workflow_previous_allowed")
    date_deadline = fields.Date(string="Achievement Deadline", readonly=True)
    deadline_exceeded = fields.Boolean(string="Deadline Exceeded", compute="_compute_deadline_exceeded")
    delayed = fields.Date(string="Achievement Deadline delay", readonly=True)
    auto_workflow_next_after_deadline = fields.Boolean(
        string="Pass to next stage automatically after deadline?", readonly=True
    )
    is_allow_move_other_stage = fields.Boolean("إمكانية الانتقال الى مرحلة اخري")
    company_notes = fields.Char("ملاحظات شركة التوثيق")

    current_employee = fields.Many2one(
        "hr.employee", string="Current employee", compute="find_current_employee", tracking=True
    )
    current_department = fields.Many2one(
        "hr.department", string="current department", compute="find_current_department", tracking=True
    )

    current_user = fields.Many2one("hr.employee", string="Current user", readonly=True, copy=False)
    employee_assigned = fields.Boolean(
        string="Employee assigned", compute="current_employee_is_assigned", tracking=True)

    """
    This field computes the users that do have access to the current request by the fact of being a member of
    the current or prior stages.
    """
    stage_security_users_ids = fields.Many2many('res.users', compute="_compute_stage_security_users_ids", store=True)


    def check_next_stage_permission(self):
        user_id = self.env.user
        next_stage = self.stage_id
        # check if user have permission to pass to this stage
        employee_obj = self.env["hr.employee"].search([("user_id", "=", user_id.id)])
        if (
                user_id in [employee_id.user_id for employee_id in next_stage.employee_ids]
                or employee_obj.department_id in next_stage.department_ids
                or user_id.groups_id in next_stage.group_ids
                or next_stage.group_ids in user_id.groups_id
        ):
            self.next_stage_permission = True

        next_second_stage = self.current_second_stage
        if (
                user_id in [employee_id.user_id for employee_id in next_second_stage.employee_ids]
                or employee_obj.department_id in next_second_stage.department_ids
                or user_id.groups_id in next_second_stage.group_ids
                or next_second_stage.group_ids in user_id.groups_id
        ):
            self.next_second_stage_permission = True


    def check_refuse_stage_permission(self):
        user_id = self.env.user
        refuse_stage = self.stage_ids.search([("is_refuse_type", "=", True)], limit=1)
        employee_obj = self.env["hr.employee"].search([("user_id", "=", user_id.id)])

        if (
                user_id in [employee_id.user_id for employee_id in refuse_stage.employee_ids]
                or employee_obj.department_id in refuse_stage.department_ids
                or user_id.groups_id in refuse_stage.group_ids
                or refuse_stage.group_ids in user_id.groups_id
        ):
            self.refuse_stage_permission = True

    def workflow_previous(self):
        for rec in self:
            rec.ensure_one()
            rec._on_workflow_previous()
            previous_stage_ids = rec._get_previous_stages()
            context = {"previous_stage_ids": previous_stage_ids, "default_contract_id": rec.id}
            context.update(rec.env.context)

            return {
                "type": "ir.actions.act_window",
                "name": "Previous Stage",
                "res_model": "dynamic.workflow.contract.stage.previous.wizard",
                "view_type": "form",
                "view_mode": "form",
                "target": "new",
                "context": context,
            }

    @api.depends("stage_id")
    def check_current_stage_have_secondary_stage(self):
        for rec in self:
            if rec.secondary_stage_ids:
                rec.have_secondary_stage = True
            else:
                rec.have_secondary_stage = False

    @api.depends("date_deadline")
    def _compute_deadline_exceeded(self):
        today = fields.Date.from_string(fields.Date.context_today(self))
        for rec in self:
            if rec.date_deadline:
                date_deadline = fields.Date.from_string(rec.date_deadline)
                if date_deadline < today:
                    rec.deadline_exceeded = True

    @api.depends()
    def current_employee_is_assigned(self):
        for rec in self:
            if self.env.user.id == rec.current_user.user_id.id:
                rec.employee_assigned = True
            else:
                rec.employee_assigned = False


    def _compute_related_stages(self):
        for rec in self:
            visible_stages = rec._get_visible_stages()
            rec.related_stages = str(visible_stages and visible_stages.ids or [])
            related_secondary_stages = rec.secondary_stage_ids.ids
            rec.related_secondary_stages = str(related_secondary_stages)

    def find_current_employee(self):
        for rec in self:
            rec.current_employee = self.env["hr.employee"].search([("user_id", "=", self.env.user.id)])

    def find_current_department(self):
        for rec in self:
            rec.current_department = self.env["hr.employee"].search(
                [("user_id", "=", self.env.user.id)]).department_id


    def _compute_stage_ids(self):
        for rec in self:
            rec.stage_ids = rec.project_type.stage_ids


    def _get_visible_stages(self):
        self.ensure_one()
        return self.stage_ids.filtered(lambda r: r.is_first_type == False and r.is_refuse_type == False)


    def _compute_is_assign_employee_allowed(self):
        for rec in self:
            if (
                    not rec.stage_id
                    or rec.is_stage_refuse
                    or rec.is_stage_success
                    or (rec.have_secondary_stage and not rec.designation_secondary_stage)
                    or (not rec.have_secondary_stage and not rec.designation)
            ):
                rec.is_assign_employee_allowed = False
                continue
            if rec.designation_secondary_stage and rec.current_employee not in rec.current_second_stage.employee_ids:
                rec.is_assign_employee_allowed = False
                continue
            rec.is_assign_employee_allowed = True


    def _compute_is_assign_office_allowed(self):
        for rec in self:
            if (
                    not rec.stage_id
                    or rec.is_stage_refuse
                    or rec.is_stage_success
                    or (rec.have_secondary_stage and not rec.designation_office_secondary_stage)
                    or (not rec.have_secondary_stage and not rec.designation_office)
            ):
                rec.is_assign_office_allowed = False
                continue
            if rec.designation_office_secondary_stage and rec.current_employee not in rec.current_second_stage.employee_ids:
                rec.is_assign_office_allowed = False
                continue
            rec.is_assign_office_allowed = True


    def _compute_is_refuse_action_allowed(self):
        for rec in self:
            if (
                    not rec.stage_id
                    or rec.is_stage_refuse
                    or rec.is_stage_success
                    # [FIXME] shaimaa or not rec.refuse_stage_permission
                    or (not rec.is_assign_employee_allowed and not rec.is_workflow_next_allowed)
            ):
                rec.is_refuse_action_allowed = False
            else:
                rec.is_refuse_action_allowed = True


    def _compute_is_return_action_allowed(self):
        for rec in self:
            if (
                    not rec.stage_id
                    or rec.is_stage_first
                    or rec.is_stage_refuse
                    or rec.is_stage_success
                    or not rec.stage_id.is_return_to_investor_stage
            ):
                rec.is_return_action_allowed = False
            else:
                rec.is_return_action_allowed = True


    def _compute_is_workflow_next_allowed(self):
        for rec in self:
            if (
                    rec.is_stage_refuse
                    or rec.is_stage_success
                    or not rec.stage_id
                    or rec.is_assign_employee_allowed
                    # [FIXME] shaimaa or (not rec.next_stage_permission and not rec.next_second_stage_permission)
            ):
                rec.is_workflow_next_allowed = False
            else:
                rec.is_workflow_next_allowed = True


    def _compute_is_workflow_previous_allowed(self):
        for rec in self:
            if not rec._get_previous_stages():
                rec.is_workflow_previous_allowed = False
            else:
                if (
                        rec.is_stage_first
                        or rec.is_stage_refuse
                        or rec.is_stage_success
                        or not rec.stage_id
                        or (not rec.is_workflow_next_allowed and not rec.is_assign_employee_allowed)
                ):
                    rec.is_workflow_previous_allowed = False
                else:
                    rec.is_workflow_previous_allowed = True


    @api.depends('stage_ids', 'stage_id')
    def _compute_stage_security_users_ids(self):
        users_related = []

        for stage in self.stage_ids:
            if self.stage_id.sequence >= stage.sequence:
                _logger.debug('Stage ' + str(stage) + ' is prior or equal to current one.')
                for employee in stage.employee_ids:
                    users_related.append(employee.user_id.id)

        if users_related:
            self.stage_security_users_ids = [(6, False, users_related)]

        return True


    def workflow_init(self):
        self.ensure_one()
        if not self.stage_id:
            self.stage_id = self.stage_ids and self.stage_ids[0] or False

    @api.model
    def _get_first_stage(self):
        stage_ids = self.env['workflow.project.type'].search([("code", "=", 'contract')]).stage_ids
        if stage_ids:
            return stage_ids[0]
        else:
            return False


    def _get_previous_stages(self):
        self.ensure_one()
        previous_stage_ids = []
        for stage in self._get_visible_stages():
            if stage != self.stage_id:
                previous_stage_ids.append(stage.id)
            else:
                break
        if self.secondary_stage_ids:
            for stage in self.secondary_stage_ids:
                if stage != self.current_second_stage:
                    previous_stage_ids.append(stage.id)
                else:
                    break
        return previous_stage_ids


    def _on_workflow_next(self):
        self.ensure_one()
        self.write(
            {
                "date_deadline": False,

                "current_user": False,
                "auto_workflow_next_after_deadline": False,
            }
        )
        self.set_value_to_date_deadline_stage()


    def _on_workflow_previous(self):
        self.ensure_one()
        self.write(
            {
                "date_deadline": False,
                "current_user": False,
                "auto_workflow_next_after_deadline": False,
            }
        )
        self.set_value_to_date_deadline_stage()


    def set_value_to_date_deadline_stage(self):
        self.ensure_one()
        if not self.designation:
            if not self.current_second_stage:
                achievement_duration = self.stage_id.achievement_duration
            else:
                achievement_duration = max(
                    self.stage_id.achievement_duration,
                    self.current_second_stage.achievement_duration,
                )
            today = fields.Date.from_string(fields.Date.context_today(self))
            today_ds = datetime.now().replace(second=0, microsecond=0)
            today_ds.strftime("%d/%m/%Y %H:%M:%S")
            check_day_in_weekdays = convert_date_to_dayinweek(str(today_ds))
            if check_day_in_weekdays == 'Thursday':
                achievement_duration = achievement_duration + 2
            self.date_deadline = today + relativedelta(days=achievement_duration)


    def workflow_next(self):
        self.ensure_one()

        self._on_workflow_next()

        if self.secondary_stage_ids:
            return self.workflow_next_secondary_stage()

        return self.workflow_next_stage()


    def action_move_other_stage(self):
        self.ensure_one()
        if self.is_allow_move_other_stage:
            self._on_workflow_next()
            self.current_second_stage = self.current_second_stage.parent_id.id
            user_id = self.env.user


    def workflow_next_stage(self):
        stage_ids = self.stage_ids.filtered(lambda r: r.is_refuse_type == False)
        # search and go to the next stage
        for stage, value in enumerate(stage_ids, 1):
            if self.stage_id.id == value.id:
                if self.stage_ids[stage - 1].send_request_to_direct_manager:
                    try:
                        if self.env.user.employee_ids.parent_id:
                            self.stage_id = stage_ids[stage]
                            self.current_user = self.env.user.employee_ids.parent_id
                            if self.secondary_stage_ids:
                                self.current_second_stage = self.secondary_stage_ids[0].id
                        else:
                            raise Exception
                    except Exception as e:
                        raise ValidationError("يجب إسناد مدير مباشر للموظف الحالي.")
                    break
                else:
                    self.stage_id = stage_ids[stage]
                    if stage_ids[stage].contract_state:
                        self.state = stage_ids[stage].contract_state

                    if self.secondary_stage_ids:
                        self.current_second_stage = self.secondary_stage_ids[0].id

                    break

    def workflow_next_secondary_stage(self):
        stage_ids = self.secondary_stage_ids

        # search and go to the next stage
        if stage_ids and not self.current_second_stage:
            self.current_second_stage = stage_ids[0]
        for stage, value in enumerate(stage_ids, 1):
            if self.current_second_stage.id == value.id:
                if stage != len(stage_ids):
                    if stage_ids[stage - 1].send_request_to_direct_manager:
                        try:
                            if self.env.user.employee_ids.parent_id:
                                self.current_second_stage = stage_ids[stage]
                                self.current_user = self.env.user.employee_ids.parent_id
                            else:
                                raise Exception
                        except Exception as e:
                            raise ValidationError("يجب إسناد مدير مباشر للموظف الحالي.")
                    else:
                        self.current_second_stage = stage_ids[stage]
                    break
                else:
                    self.workflow_next_stage()
                    user_id = self.env.user

                break

    def workflow_prev_stage(self):
        stage_ids = self.stage_ids
        # search and go to the next stage
        for stage, value in enumerate(stage_ids, 1):
            if self.stage_id.id == value.id:
                self.stage_id = stage_ids[stage - 2]

                break

    """
    End workflow ( المراحل )
    """


class hrPayrollWageHistory(models.Model):
    _name = 'hr.payroll.wage.history'
    _order = 'effective_date desc, id desc'
    _description = 'Payroll Wage History'

    name = fields.Char(string='Revision No', size=20, readonly=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, readonly=True)
    contract_id = fields.Many2one(
        'hr.contract', string='Contract', readonly=True)
    cur_grade_level_id = fields.Many2one(comodel_name='hr.grade.level', string=" Current Grade")
    pre_grade_level_id = fields.Many2one(comodel_name='hr.grade.level', string="Previous Grade")

    department_id = fields.Many2one(
        'hr.department', string='Department', readonly=True)
    job_id = fields.Many2one('hr.job', string='Job Title', readonly=True)
    pre_wage = fields.Float(
        string='Previous Wage', required=True, readonly=True)
    cur_wage = fields.Float(
        string='Current Wage', required=True, readonly=True)
    difference = fields.Float(string='Difference',
                              compute='_compute_wage_diff', store=True)
    percentage = fields.Float(string='Percentage',
                              compute='_compute_percentage', store=True)
    effective_date = fields.Date(string='Effective Date', required=True,
                                 default=fields.Date.context_today)
    responsible_id = fields.Many2one(
        'res.users', string='Responsible Manager', readonly=True)
    eff_month = fields.Char(string="Effective Month",
                            compute='_get_month_year', store=True)
    eff_year = fields.Char(string="Effective Year",
                           compute="_get_month_year", store=True)
    until_eff_date = fields.Integer(string='Months until Effective Date',
                                    compute='_get_months_until_eff_date')
    state = fields.Selection(string='State',
                             selection=[('ok', 'OK'),
                                        ('cancel', 'Cancel')],
                             default='cancel')

    #     order_by = fields.Char(string='Order By', compute='_get_order')
    #
    #     def _get_order(self):
    #         self.order_by = self.env['hr.payroll.wage.history.report'].order_by

    def _get_months_until_eff_date(self):
        for x in self:
            format = '%Y-%m-%d'
            #             m = int(datetime.strptime(x.effective_date, format).month)
            #             temp_date = datetime.now() + relativedelta(months=-m)
            x.until_eff_date = int(
                (relativedelta.relativedelta(datetime.now(),
                                             datetime.strptime(str(x.effective_date), format))).months)

    """"
    @api.depends('pre_wage', 'cur_wage')
    def _compute_wage_diff(self):
    
           Compute Wage Difference
        
        for x in self:
            x.difference = x.cur_wage - x.pre_wage
            if x.difference < 0:
                raise Warning('Current Wage must larger than Previous Wage')
    """

    @api.depends('pre_wage', 'cur_wage')
    def _compute_percentage(self):
        """
            Compute Percentage
        """
        for x in self:
            x.percentage = x.pre_wage > 0 and 100 * \
                           (x.cur_wage - x.pre_wage) / x.pre_wage or 0

    def _get_month_year(self):
        """
            Compute Effective Month and Year for Filter
        """
        for x in self:
            x.eff_month = str(
                datetime.strptime(str(x.effective_date), '%Y-%m-%d').month)
            x.eff_year = str(datetime.strptime(str(x.effective_date), '%Y-%m-%d').year)

    @api.model
    def search(self, args, offset=0, limit=None, order='effective_date DESC', count=False):
        """
            Overide Search Method
            This is the core of displaying the Record 
            and setting up Context
        """
        context = self._context
        results = []
        # Filter for Highest Raise in 12 months
        if context.get('filter_highest_raise', False):
            self._cr.execute("""SELECT id FROM hr_payroll_wage_history
                     WHERE difference IN
                     (SELECT MAX(difference)
                     FROM hr_payroll_wage_history
                     WHERE pre_wage > 0 
                     AND effective_date >= (CURRENT_DATE - INTERVAL '12 MONTH'))""")
            record_ids = self._cr.fetchall()

            for record in record_ids:
                results.append(record[0])
            args.append(('id', 'in', results))
        # Filter for No Raise Salary in 12 months
        if context.get('filter_no_raise', False):
            self._cr.execute("""SELECT id FROM hr_payroll_wage_history
                    WHERE difference = 0
                    AND effective_date >= (CURRENT_DATE - INTERVAL '12 MONTH')""")
            record_ids = self._cr.fetchall()

            for record in record_ids:
                results.append(record[0])
            args.append(('id', 'in', results))

        if context.get('order_by', False):
            order = context.get('order_by')

        return super(hrPayrollWageHistory, self).search(
            args, offset=offset, limit=limit, order=order, count=count)

class HrPayslipEmployee(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    @api.model
    def _get_previous_employees(self):
        gp_rec = self.env['hr.payslip.run'].browse(self._context.get('active_id', False))
        emp_ids = []
        for l in gp_rec.slip_ids:
            if l.employee_id.id not in emp_ids:
                emp_ids.append(l.employee_id.id)
        return [(6, 0, emp_ids)]

    p_employee_ids = fields.Many2many('hr.employee', 'hr_p_employee_group_rel', 'p_payslip_id', 'p_employee_id',
                                      default=_get_previous_employees, string='Previous Employees')

class HREmployeeAttachments(models.Model):
    _name = "hr.employee.attachments"
    _description = "Hr Employee Attachments"

    name = fields.Char(string='اسم المرفق', required=True)
    attachment_id = fields.Binary(string="المرفق", required=True)
    attachment_filename = fields.Char(string='اسم المرفق')
    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee")