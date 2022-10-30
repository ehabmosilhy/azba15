# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
def convert_date_to_dayinweek(date):
    formatted_date = datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
    day_in_week = formatted_date.strftime("%A")
    return day_in_week

class EmployeePromotion(models.Model):
    _name = 'employee.promotion'
    _description = 'Employee Promotion'
    _inherit = ['mail.thread']

    name = fields.Char('Seq Number', readonly=True)
    date = fields.Date('Date', default=fields.Datetime.now)
    promotions_ids = fields.One2many('promotion.line', 'employee_promotion_id', 'Suggested Promotions')

    state = fields.Selection(string='Status', selection=[
        ('dept_manager', 'مدراء الوحدات الإدارية'),
        ('hr_specialist', 'أخصائي الموارد البشرية'),
        ('support_service', 'مدير إدارة الخدمات المساندة'),
        ('office_leader', 'قائد المكتب'),
        ('promotion_done', 'تم'),
        ('refuse', 'مرفوض')],
                             readonly=True,
                             default='dept_manager')
    return_reason = fields.Char(string="سبب الإرجاع", tracking=True)
    returned_by = fields.Many2one("res.users", string="Returned by", tracking=True)
    is_returned = fields.Boolean()
    return_message = fields.Text("Refuse message", tracking=True)
    refuse_reason = fields.Char("سبب الرفض", tracking=True)
    refuse_stage = fields.Many2one("dynamic.workflow.stage", string="Refuse stage", tracking=True)
    rejected_by = fields.Many2one("res.users", string="Rejected by")

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('employee.promotion')
        result = super(EmployeePromotion, self).create(vals)

        return result


    def button_create_promotion_lines(self):
        line_ids = []
        format = '%Y-%m-%d'
        self.promotions_ids.unlink()
        actual_date = datetime.strptime(str(self.date), format) + relativedelta(years=-4, days=+44)
        contracts = self.env['hr.contract'].search(['|', ('employee_id.date_grade_update', '<=', str(actual_date)),
                                                    '&', ('employee_id.date_of_join', '<=', str(actual_date)),
                                                    ('employee_id.date_grade_update', '=', False)])

        for contract in contracts:
            current_employee_salary_type = contract.grade_level_id.grade_id.grade_type_id
            current_employee_grade = contract.grade_level_id
            # current_employee_level = contract.grade_level_id.grade_id
            current_level_sequence = contract.grade_level_id.level_sequence

            next_level = self.env['hr.grade.level'].search(
                [('grade_type_id', '=', current_employee_salary_type.id),
                 ('level_sequence', '>', current_level_sequence),
                 ('gross', '>', current_employee_grade.gross),
                 ], limit=1)

            if next_level:
                line_ids.append((0, 0, {
                    'employee_id': contract.employee_id.id,
                    'promotion_level_id': next_level.id,
                    'employee_promotion_id': self.id
                }))
        self.promotions_ids = line_ids

    #
    # def button_approved_by_hr_specialist(self):
    #     for record in self:
    #         record.state = 'approved_by_hr_specialist'

    #
    # def button_approved_by_promotion_group(self):
    #     for record in self:
    #         record.state = 'approved_by_promotion_group'

    def action_hr_specialist(self):
        for record in self:
            record.state = 'hr_specialist'
    def action_support_service(self):
        for record in self:
            record.state = 'support_service'
    def action_office_leader(self):
        for record in self:
            record.state = 'office_leader'

    def onchange_house_allow1(self, has_housing_allow=False, wage=0.00):
        if has_housing_allow:
            housing_allow = wage * 3 / 12

            if housing_allow > 2000:
                housing_allow = 2000
            elif 1000 > housing_allow > 0:
                housing_allow = 1000
            return housing_allow
        else:
            return 0.0


    def action_promotion_done(self):
        for record in self:
            format = '%Y-%m-%d'

            for line in self.promotions_ids:
                line.contract_id.grade_level_id = line.promotion_level_id
                line.employee_id.date_grade_update = fields.Datetime.now()
                line.contract_id.hosing_allowancme = self.onchange_house_allow1(line.contract_id.has_housing_allow, line.contract_id.wage)
            record.state = 'promotion_done'


    def button_refuse(self):
        for record in self:
            record.state = 'refuse'

    """
    Start workflow fields ( حقول المراحل )
    """
    category = fields.Many2one("dynamic.workflow.category", string="Category", tracking=True)

    project_type = fields.Many2one("workflow.project.type", string="Project type", tracking=True,
                                   default=lambda self: self.env.ref(
                                       'ejad_erp_hr.promotion_project_type_data').id)
    project_code = fields.Char(related="project_type.code")

    stage_ids = fields.Many2many("dynamic.workflow.stage", compute="_compute_stage_ids", tracking=True)
    # stage_id = fields.Many2one("dynamic.workflow.stage", string="المرحلة", tracking=True,
    #                            default=lambda self: self.env.ref('ejad_erp_hr.dynamic_workflow_stage_data_0').id)
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
    next_second_stage_permission = fields.Boolean("Next stage second permission", compute="check_next_stage_permission")
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
    delayed = fields.Date(string="Achievement Deadline Delay", readonly=True)
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
        self.ensure_one()
        self._on_workflow_previous()
        previous_stage_ids = self._get_previous_stages()
        context = {"previous_stage_ids": previous_stage_ids, "default_promotion_id": self.id}
        context.update(self.env.context)

        return {
            "type": "ir.actions.act_window",
            "name": "Previous Stage",
            "res_model": "dynamic.workflow.promotion.stage.previous.wizard",
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
                    if stage_ids[stage].promotion_state:
                        self.state = stage_ids[stage].promotion_state
                        if self.state == 'promotion_done':
                            self.button_approved_by_manager()

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


class PromotionLines(models.Model):
    _name = 'promotion.line'
    _description = 'Promotion Lines'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    contract_id = fields.Many2one('hr.contract', related='employee_id.contract_id')
    current_employee_level_id = fields.Many2one('hr.grade.level', string="Current Grade/Level",
                                                compute='_compute_current_employee_contract', store=True)
    promotion_level_id = fields.Many2one('hr.grade.level', string="Promotion Grade/level")
    employee_promotion_id = fields.Many2one('employee.promotion', string="Promotion Request", ondelete="set null")


    @api.depends('employee_id')
    def _compute_current_employee_contract(self):
        for record in self:
            record.current_employee_level_id = record.contract_id.grade_level_id
