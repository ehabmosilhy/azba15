4  # 4fwfr -*- coding: utf-8 -*-
# end of service

import logging
from datetime import datetime
from odoo import api, fields, models, _, exceptions
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
def convert_date_to_dayinweek(date):
    formatted_date = datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
    day_in_week = formatted_date.strftime("%A")
    return day_in_week



class EndOfService(models.Model):
    _name = 'hr.end.service'
    _rec_name = 'name'
    _description = 'end of service'
    _inherit = ['mail.thread']

    name = fields.Char('name', tracking=True, required=False, readonly=True)

    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)

    employee_id = fields.Many2one('hr.employee', string='اسم الموظف', tracking=True)
    department_id = fields.Many2one('hr.department', string="القسم", tracking=True)
    job_id = fields.Many2one('hr.job', string="الوظيفه", required=True, tracking=True)
    contract_type = fields.Selection([('sicetific', 'هيئة علمية '),
                                      ('management', 'ادارين'),
                                      ('staff', 'مهنين')], string="نوع العقد", tracking=True)
    type = fields.Selection(related='employee_id.emp_type', tracking=True)
    grade_id = fields.Many2one('hr.grade', string='المرتبة الوظيفيه', tracking=True)
    grade_level_id = fields.Many2one('hr.grade.level', tracking=True, string='الدرجة الوظيفيه')
    date_start = fields.Date('ناريخ التعيين', required=True,
                             help="Start date of the contract.", tracking=True)
    date_end = fields.Date('تاريخ انتهاء العقد',
                           help="End date of the contract .", default=fields.Date.today, tracking=True)
    date_benefit = fields.Date('تاريخ الاعداد', default=fields.Date.today,
                               help="benefit date of the employee.", tracking=True)

    benefits = fields.Float('مبلغ الاستحقاق', digits=(16, 2), required=True, tracking=True,
                            help="Employee's  [[benefits.")
    responsible = fields.Many2one('res.users', string='الموظف المسؤول', default=lambda self: self.env.user,
                                  tracking=True)
    identification_id = fields.Char(string='رقم الهوية', groups="hr.group_hr_user")
    salary = fields.Float('basic salary ', tracking=True)
    end_service_months = fields.Integer('عدد أشهر نهاية الخدمة', readonly=False)
    ens_months_c = fields.Integer(string='عدد اشهر نهاية الخدمة', store=True, compute='get_ens_months')
    move_id = fields.Many2one('account.move', string="قيد اليومية", readonly=True)
    payment_type2 = fields.Selection([('bank', 'تحويل بنكي'), ('check', 'شيك'), ('cash', 'صندوق (نقد)')],
                                     default='bank', string='نوع السداد')
    journal_id = fields.Many2one('account.journal', string="طريق السداد ", domain=[('type', 'in', ('bank', 'cash'))])
    treasury_account_id = fields.Many2one('account.account', related="journal_id.default_account_id",
                                          string="الحساب الدائن")
    benefit_account_id = fields.Many2one('account.account', default=lambda self: self.env.user.company_id.benefit_account_id,
                                          string="الحساب المدين")
    bank_ref = fields.Char('رقم السند')
    bank_check_no = fields.Char('رقم الشيك')
    bank_ref_seq = fields.Char('Bank Reference Seq')
    cash_ref_seq = fields.Char('cash Reference Seq')
    refuse_reason = fields.Char("سبب الرفض", tracking=True)
    refuse_stage = fields.Many2one("dynamic.workflow.stage", string="Refuse stage", tracking=True)
    rejected_by = fields.Many2one("res.users", string="Rejected by")


    @api.depends('end_service_months')
    def get_ens_months(self):
        for rec in self:
            rec.ens_months_c = rec.end_service_months or 0

    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('employee_request', 'Apply Request'),
        ('approved_by_hr', 'Confirmed HR'),
        ('accountant', 'confirm Accountant'),
        ('financial_auditor', 'Confirm Financial Auditor'),
        ('financial_manager', 'Confirm Financial Manager'),
        ('financial_monitor', 'Confirm Financial Monitor'),
        ('admin_financial_manager', 'Confirm administrative and Financial Manger'),
        ('general_director_approve', 'General director approve'),
        ('benefits_paid', 'Paid'),
        ('cancel', 'Cancel')],
                             readonly=True,
                             default='draft')

    require_general_director_approve = fields.Boolean(string='يحتاج موافقة الرئيس',
                                                      compute='_compute_is_exceed_max_amount')
    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)


    @api.depends('benefits')
    def _compute_is_exceed_max_amount(self):
        for record in self:
            if record.benefits <= record.company_id.max_amount_require_director_approval:
                record.require_general_director_approve = False
            else:
                record.require_general_director_approve = True

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].with_context(ir_sequence_date=vals.get('payment_date')).next_by_code(
            'hr.end.of.service')

        result = super(EndOfService, self).create(vals)
        return result

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            if self.type in ['basic', 'Retired']:
                self.salary = self.employee_id.grade_level_id.gross
                self.date_start = self.employee_id.date_of_join
                self.grade_id = self.employee_id.grade_id
                self.grade_level_id = self.employee_id.grade_level_id
                self.job_id = self.employee_id.job_id
                self.contract_type = self.employee_id.contract_type
                self.department_id = self.employee_id.department_id
                self.identification_id = self.employee_id.identification_id
                # self.name = str(self.employee_id.name) + ' ' + str(self.employee_id.grade_id.name)
                self.calculate_reword()
            else:
                raise exceptions.ValidationError(_('هذا الموظف ليس اساسي'))

    @api.onchange('date_end', 'date_start')
    def calculate_reword(self):
        if self.salary:
            salary = self.salary
            date_end = str(self.date_end)
            date_start = str(self.date_start)
            if ((datetime.strptime(date_end, '%Y-%m-%d') - (
                    datetime.strptime(date_start, '%Y-%m-%d'))).days / 354) >= 1:
                if (datetime.strptime(date_start, '%Y-%m-%d')) < (datetime.strptime('1999-01-01', '%Y-%m-%d')):

                    service_months_double = ((datetime.strptime('1999-01-01', '%Y-%m-%d')) - (
                        datetime.strptime(date_start, '%Y-%m-%d'))).days / 354 * 2

                    service_months = ((datetime.strptime(date_end, '%Y-%m-%d')) - (
                        datetime.strptime('1999-01-01', '%Y-%m-%d'))).days / 354
                    self.end_service_months = int(service_months_double + service_months)
                    self.benefits = self.end_service_months * salary
                else:
                    service_months_number = ((datetime.strptime(date_end, '%Y-%m-%d')) - (
                        datetime.strptime(date_start, '%Y-%m-%d'))).days / 354
                    self.end_service_months = int(service_months_number)

                    self.benefits = self.end_service_months * salary
            else:
                raise exceptions.ValidationError(_('هذا الموظف لم يكمل العام'))

    #
    # def button_employee_send_request(self):
    #     for record in self:
    #         record.state = 'employee_request'
    #
    #
    # def button_approved_by_hr(self):
    #     for record in self:
    #         record.state = 'approved_by_hr'

    def check_bank_cash_ref(self):
        if self.payment_type2 == 'bank':
            if not self.bank_ref_seq:
                bank_ref_seq = self.env['ir.sequence'].next_by_code('payment.bank.seq')
                self.bank_ref_seq = bank_ref_seq
                self.bank_ref = bank_ref_seq
            else:
                self.bank_ref = self.bank_ref_seq

        elif self.payment_type2 == 'cash':
            if not self.cash_ref_seq:
                cash_ref_seq = self.env['ir.sequence'].next_by_code('payment.cash.seq')
                self.cash_ref_seq = cash_ref_seq
                self.bank_ref = cash_ref_seq
            else:
                self.bank_ref  = self.cash_ref_seq

        else:
            self.bank_ref = self.bank_ref or False

    #
    # def button_accountant(self):
    #     for record in self:
    #         record.check_bank_cash_ref()
    #         record.state = 'accountant'
    #
    #
    # def button_draft(self):
    #     for rec in self:
    #         rec.state = 'draft'



    def button_financial_auditor(self):
        for rec in self:
            rec.check_bank_cash_ref()
            # rec.state = 'financial_auditor'
            debit = credit = rec.benefits or 0.00

            if not rec.journal_id.id:
                raise UserError(_("Please choose the journal"))

            move = {
                'name': '/',
                'move_type': 'entry',
                'journal_id': rec.journal_id.id,
                'ref': self.name + ' مكافئة  ',
                'date': fields.Date.today(),
                'bank_account_info': rec.employee_id.bank_account_id.acc_number,

                'line_ids': [(0, 0, {
                    'name': rec.name or '/' + self.employee_id.name + "   - مكافئة نهاية الخدمة ",
                    'debit': debit,
                    'account_id': rec.company_id.benefit_account_id.id,
                    'partner_id': rec.employee_id.user_id.partner_id.id,
                }), (0, 0, {
                    'name': rec.name or '/' + self.employee_id.name + "   - مكافئة نهاية الخدمة ",
                    'credit': credit,
                    'account_id': rec.journal_id.default_account_id.id,
                    'partner_id': rec.employee_id.user_id.partner_id.id,
                })]
            }
            move_id = self.env['account.move'].create(move)
            move_id.post()
            #self.journal_id = self.journal_id
            self.move_id = move_id.id

    #
    # def button_financial_manager(self):
    #     for record in self:
    #         record.check_bank_cash_ref()
    #         record.state = 'financial_manager'
    #
    #
    # def button_financial_monitor(self):
    #     for record in self:
    #         record.check_bank_cash_ref()
    #         record.state = 'financial_monitor'

    #
    # def button_admin_financial_manager(self):
    #     for record in self:
    #         record.check_bank_cash_ref()
    #         record.state = 'admin_financial_manager'

    #
    # def button_general_director_approve(self):
    #     for record in self:
    #         record.check_bank_cash_ref()
    #         record.state = 'general_director_approve'


    #
    # def button_mandat_amount_paid(self):
    #     for record in self:
    #         record.check_bank_cash_ref()
    #         record.state = 'benefits_paid'

    #
    # def button_cancel(self):
    #     for record in self:
    #         record.state = 'cancel'
    #         if record.move_id:
    #             record.move_id.journal_id.update_posted = True
    #             record.move_id.button_cancel()
    #             record.move_id.unlink()

    """
    Start workflow fields ( حقول المراحل )
    """
    category = fields.Many2one("dynamic.workflow.category", string="Category", tracking=True)

    project_type = fields.Many2one("workflow.project.type", string="Project type", tracking=True,
                                   default=lambda self: self.env.ref(
                                       'ejad_erp_hr.endofservice_project_type_data').id)
    project_code = fields.Char(related="project_type.code")

    stage_ids = fields.Many2many("dynamic.workflow.stage", compute="_compute_stage_ids", tracking=True)
    # stage_id = fields.Many2one("dynamic.workflow.stage", string="المرحلة", tracking=True,
    #                            default=lambda self: self.env.ref('ejad_erp_hr.dynamic_workflow_stage_data_0').id)
    stage_id = fields.Many2one("dynamic.workflow.stage", string="المرحلة")
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
        context = {"previous_stage_ids": previous_stage_ids, "default_endofservice_id": self.id}
        context.update(self.env.context)

        return {
            "type": "ir.actions.act_window",
            "name": "Previous Stage",
            "res_model": "dynamic.workflow.endofservice.stage.previous.wizard",
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
                    if stage_ids[stage].endofservice_state:
                        self.state = stage_ids[stage].endofservice_state
                        if self.state == 'financial_auditor':
                            self.check_bank_cash_ref()
                            self.button_financial_auditor()
                        elif self.state in ('accountant', 'financial_manager', 'financial_manager', 'financial_monitor',
                                           'admin_financial_manager', 'general_director_approve', 'benefits_paid'):
                            self.check_bank_cash_ref()

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


