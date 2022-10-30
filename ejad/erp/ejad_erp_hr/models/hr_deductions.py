# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
import logging
_logger = logging.getLogger(__name__)

from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
def convert_date_to_dayinweek(date):
    formatted_date = datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
    day_in_week = formatted_date.strftime("%A")
    return day_in_week


class hr_deductions_type(models.Model):
    _name = 'hr.deductions.type'
    _description = 'Hr Deductions Type'

    name = fields.Char(string="Name", required=True)
    rule_id = fields.Many2one('hr.salary.rule', string='Rule salary ', required=True)
    deduction_type = fields.Selection(string="أنواع الحسميات", required=True,
                                      selection=[('another', 'حسمية آخرى'), ('reward', 'حسمية مكافأت'),
                                                 ('attendance', 'حسمية حضور و انصراف')])
    reward_dean_of_college_center = fields.Boolean('مكافأة منصب عميد كلية أو عمادة مركز')
    reward_deputy_college_center = fields.Boolean('مكافأة منصب وكيل كلية أو وكيل مركز')
    reward_admin_college_center = fields.Boolean('مكافأة منصب أمين كلية او مركز')
    reward_manager_college = fields.Boolean('مكافأة منصب رئيس قسم علمي (كليات فقط)')
    reward_security_department = fields.Boolean('مكافأة قسم الأمن والسلامة (الشؤون العامة)')
    reward_reception_department = fields.Boolean('مكافأة قسم الإستقبال و السنترال  (الضيافة والإسكان)')
    reward_financial_department = fields.Boolean('مكافأة قسم الصندوق (الإدارة المالية)')
    reward_government_relation = fields.Boolean('مكافأة مندوب علاقات حكومية')
    reward_calling = fields.Boolean('مكافأة بدل اتصال (بعض الموظفين)')
    reward_passport_representative_external = fields.Boolean('مكافأة مندوب جوازات خارجي')
    reward_passport_representative_internal = fields.Boolean('مكافأة مندوب جوازات داخلي')
    reward_purchase_representative = fields.Boolean('مكافأة مندوب مشتريات')
    reward_revenue_collector = fields.Boolean('مكافأة محصل إيرادات')
    other_reward = fields.Boolean('مكافأة أخرى')
    food_reward = fields.Boolean('مكافأة طعام')

    @api.constrains('reward_dean_of_college_center',
                    'reward_deputy_college_center',
                    'reward_admin_college_center',
                    'reward_manager_college',
                    'reward_security_department',
                    'reward_reception_department',
                    'reward_financial_department',
                    'reward_government_relation',
                    'reward_calling',
                    'reward_passport_representative_external',
                    'reward_passport_representative_internal',
                    'reward_purchase_representative',
                    'reward_revenue_collector',
                    'other_reward',
                    'food_reward')
    def _check_reward_options(self):
        for record in self:
            deduction_obj = self.env['hr.deductions.type']
            if record.reward_dean_of_college_center:
                deduction_type_id = deduction_obj.search(
                    [('reward_dean_of_college_center', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_dean_of_college_center'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_deputy_college_center:
                deduction_type_id = deduction_obj.search(
                    [('reward_deputy_college_center', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_deputy_college_center'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_admin_college_center:
                deduction_type_id = deduction_obj.search(
                    [('reward_admin_college_center', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_admin_college_center'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_manager_college:
                deduction_type_id = deduction_obj.search(
                    [('reward_manager_college', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_manager_college'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_security_department:
                deduction_type_id = deduction_obj.search(
                    [('reward_security_department', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_security_department'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_reception_department:
                deduction_type_id = deduction_obj.search(
                    [('reward_reception_department', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_reception_department'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_financial_department:
                deduction_type_id = deduction_obj.search(
                    [('reward_financial_department', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_financial_department'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_government_relation:
                deduction_type_id = deduction_obj.search(
                    [('reward_government_relation', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_government_relation'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_calling:
                deduction_type_id = deduction_obj.search(
                    [('reward_calling', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_calling'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_passport_representative_external:
                deduction_type_id = deduction_obj.search(
                    [('reward_passport_representative_external', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_passport_representative_external'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_passport_representative_internal:
                deduction_type_id = deduction_obj.search(
                    [('reward_passport_representative_internal', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_passport_representative_internal'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_purchase_representative:
                deduction_type_id = deduction_obj.search(
                    [('reward_purchase_representative', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_purchase_representative'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.reward_revenue_collector:
                deduction_type_id = deduction_obj.search(
                    [('reward_revenue_collector', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['reward_revenue_collector'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.other_reward:
                deduction_type_id = deduction_obj.search(
                    [('other_reward', '=', True)])
                print(deduction_type_id)
                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['other_reward'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")

            if record.food_reward:
                deduction_type_id = deduction_obj.search(
                    [('food_reward', '=', True)])

                if len(deduction_type_id) > 1:
                    raise ValidationError(
                        " %s مضافة في نوع حسمية" % self._fields['food_reward'].string +
                        "اخرى ولايمكن اعادة اختيار المكافاة في نوع اخر")


class hr_deductions(models.Model):
    _name = 'hr.deductions'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "HR deductions"


    def _compute_de_amount(self):
        for rec in self:
            de_amount = 0.00
            wage = rec.wage or 0
            if rec.deducted_by == 'hours':
                hours = wage / 240
                de_amount = rec.hours_ded * hours
            if rec.deducted_by == 'days':
                days = wage / 30
                de_amount = rec.days * days
            if rec.deducted_by == 'amount':
                de_amount = rec.amount
            if rec.deducted_by == 'percentage':
                de_amount = rec.grade_level_id.gross * rec.percentage / 100

            rec.de_amount = de_amount

    name = fields.Char(string="Ref:", default="/", readonly=True)
    date = fields.Date(string="Date Request", default=fields.Date.today(), readonly=True)
    date_deducted = fields.Date(string="deducted On", required=True, default=fields.Date.today())
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    parent_id = fields.Many2one('hr.employee', related="employee_id.parent_id", string="Manager")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="Department")
    job_id = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
    # wage = fields.Float(string="Employee Salary",related="employee_id.contract_id.wage", readonly=True)
    deducted_by = fields.Selection(string='Deducted By', required=True, default='amount',
                                   selection=[('amount', 'Amount'), ('hours', 'Hours'), ('days', 'ايام'),
                                              ('percentage', 'Percentage  from salary (%)')])
    grade_level_id = fields.Many2one(comodel_name='hr.grade.level', related="employee_id.grade_level_id", readonly=True,
                                     string="Grade/Level")

    percentage = fields.Float(string="Percentage")
    days = fields.Integer(string="ايام")

    type_id = fields.Many2one('hr.deductions.type', string="نوع الحسم", required=True)
    hours_ded = fields.Float(string='Deduct Hours', help='Number of houres')
    amount = fields.Float(string=" Amount")
    de_amount = fields.Float(string="Deduct Amount", compute='_compute_de_amount')
    wage = fields.Float(string="Employee Salary", compute='_get_emp_wage', store=True)
    description = fields.Html(string='Description')
    deduction_reward_id = fields.Many2one('hr.deductions.reward')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('done', 'Done'),
    ], string="State", default='draft', tracking=True, copy=False, )
    refuse_reason = fields.Char("سبب الرفض", tracking=True)
    refuse_stage = fields.Many2one("dynamic.workflow.stage", string="Refuse stage", tracking=True)
    rejected_by = fields.Many2one("res.users", string="Rejected by")

    @api.depends('employee_id')
    def _get_emp_wage(self):
        for rec in self:
            if not rec.employee_id.contract_id.is_exceptional:
                rec.wage = rec.employee_id.contract_id.wage or 0.00
            elif rec.employee_id.contract_id.is_exceptional:
                rec.wage = rec.employee_id.contract_id.excp_wage or 0.00
            else:
                rec.wage = 0.00

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].get('hr.deductions.req') or ' '
        res = super(hr_deductions, self).create(values)
        return res


    def action_refuse(self):
        return self.write({'state': 'refuse'})


    def action_set_to_draft(self):
        return self.write({'state': 'draft'})


    def action_approve(self):
        return self.write({'state': 'approve'})


    def action_done(self):
        return self.write({'state': 'done'})

    """
    Start workflow fields ( حقول المراحل )
    """
    category = fields.Many2one("dynamic.workflow.category", string="Category", tracking=True,
                               )

    project_type = fields.Many2one("workflow.project.type", string="Project type", tracking=True,
                                   default=lambda self: self.env.ref(
                                       'ejad_erp_hr.deductions_project_type_data').id)
    project_code = fields.Char(related="project_type.code")

    stage_ids = fields.Many2many("dynamic.workflow.stage", compute="_compute_stage_ids", tracking=True,
                                 )
    # stage_id = fields.Many2one("dynamic.workflow.stage", string="المرحلة", tracking=True,
    #                            default=lambda self: self.env.ref('ejad_erp_hr.dynamic_workflow_stage_data_0').id,
    #                            translation=True)
    stage_id = fields.Many2one("dynamic.workflow.stage", string="المرحلة")

    have_secondary_stage = fields.Boolean(
        string="have secondary stage", compute="check_current_stage_have_secondary_stage"
        )
    current_second_stage = fields.Many2one(
        "dynamic.workflow.stage", string="المرحلة الفرعية الحالية", tracking=True
        )
    secondary_stage_ids = fields.One2many(related="stage_id.secondary_stage_ids", string="Secondary stages",
                                          )

    is_stage_success = fields.Boolean(related="stage_id.is_success_type")
    is_stage_refuse = fields.Boolean(related="stage_id.is_refuse_type")
    is_stage_first = fields.Boolean(related="stage_id.is_first_type")
    is_stage_cancel = fields.Boolean(related="stage_id.is_cancel_type")

    next_stage_permission = fields.Boolean("Next stage permission", compute="check_next_stage_permission",
                                           )
    next_second_stage_permission = fields.Boolean("Next stage Second permission", compute="check_next_stage_permission",
                                                  )
    precedent_stage_permission = fields.Boolean(
        "Precedent stage permission", compute="check_precedent_stage_permission"
        )
    precedent_second_stage_permission = fields.Boolean(
        "Precedent stage Second permission", compute="check_precedent_stage_permission"
        )
    refuse_stage_permission = fields.Boolean("Refuse stage permission", compute="check_refuse_stage_permission",
                                             )

    designation = fields.Boolean(related="stage_id.designation")
    designation_secondary_stage = fields.Boolean(related="current_second_stage.designation")

    designation_office = fields.Boolean(related="stage_id.designation_office")
    designation_office_secondary_stage = fields.Boolean(related="current_second_stage.designation_office",
                                                        )

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
    stage_security_users_ids = fields.Many2many('res.users', compute="_compute_stage_security_users_ids", store=True,
                                                )


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
        self.ensure_one()
        self._on_workflow_previous()
        previous_stage_ids = self._get_previous_stages()
        context = {"previous_stage_ids": previous_stage_ids, "default_deductions_id": self.id}
        context.update(self.env.context)

        return {
            "type": "ir.actions.act_window",
            "name": "Previous Stage",
            "res_model": "dynamic.workflow.deductions.stage.previous.wizard",
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
                    if stage_ids[stage].deductions_state:
                        self.state = stage_ids[stage].deductions_state

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