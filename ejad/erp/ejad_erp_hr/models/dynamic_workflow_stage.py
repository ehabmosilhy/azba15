# -*- coding: utf-8 -*-

import ast
from odoo import fields, models, api,_


class DynamicWorkflowStage(models.Model):
    _name = "dynamic.workflow.stage"
    _description = "Dynamic Workflow Stage"
    _order = "sequence"
    _inherit = ['mail.thread']

    # FIXME: This order by is very dangerous as the sequence change will affect all project type workflow
    #        salim approved this as we are in the urgent to fix the issue of not be able to change workflow order
    # TODO: 1- Add a new model dynamic.workflow.stage.sequence (project_id, stage_id, sequence)
    #       2- sequence field become a computed field with an inverse method to be able to store sequence by projetc
    #       3- Workflow next and previous method get the next stage by searching in the new relation
    #   PS: this still a half solution but quick to implement, the inconvenient that we can have only one next stage
    #   the best way to do this, is to add a new model dynamic.workflow.transition (project_id, stage_from_id, stage_to_id)

    name = fields.Char(string="Name", required=True, tracking=True, translate=True)
    technical_name = fields.Char(string="Technical name", tracking=True, translate=True)
    description = fields.Text(string="وصف المرحلة", translate=True)
    fold = fields.Boolean(string="Fold", default=True)
    sequence = fields.Integer(string="Sequence", tracking=True)
    project_type_ids = fields.Many2many(
        "workflow.project.type", "project_type_stage", "stage_id", "project_type_id"
    , translate=True)
    is_refuse_type = fields.Boolean("is refuse type", store=True, compute="onchange_stage_type_refuse")
    is_cancel_type = fields.Boolean("is cancel type", store=True, compute="onchange_stage_type_cancel")
    is_success_type = fields.Boolean("is success type", store=True, compute="onchange_stage_type_success")
    is_first_type = fields.Boolean("is first", store=True, compute="onchange_stage_type_first")
    stage_type = fields.Selection(
        [("is_first", "Is First"), ("is_success", "Is Success"), ("is_refuse", "Is Refuse"),
         ("is_cancel", "Is Cancel")],
        string="Stage Type",
        tracking=True
    , translate=True)

    #المراحل الاساسة لشاشة العقود
    contract_state = fields.Selection([
        ('draft', 'New'),
        ('open', 'Running'),
        ('pending', 'To Renew'),
        ('close', 'Expired'),
        ('cancel', 'Cancelled')
    ], string='المراحل الاساسة العقود',
        tracking=True, help='Status of the contract', translate=True)

    # المراحل الاساسة لشاشة نهاية الخدمة
    endofservice_state = fields.Selection(selection=[
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
        ('cancel', 'Cancel')], string='المراحل الاساسة لنهاية الخدمة', tracking=True, translate=True)

    # المراحل الاساسة لشاشة الترقيات
    promotion_state = fields.Selection(string='المراحل الاساسة للترقيات', selection=[
        ('draft', 'Draft'),
        ('approved_by_admin_affairs', 'Approved by Admin Affairs'),
        ('approved_by_promotion_group', 'Approved by Promotion Group'),
        ('approved_by_manager', 'Approved Administrative and Financial Manger'),
        ('promotion_done', 'Promotion Done'),
        ('refuse', 'Refused')], tracking=True, translate=True)

    # المراحل الاساسة لشاشة الحسميات
    deductions_state = fields.Selection(string='المراحل الاساسة للحسميات', selection=[
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('done', 'Done')], tracking=True, translate=True)

    # المراحل الاساسة لشاشة الانتدابات
    mandate_state = fields.Selection(string='المراحل الاساسة للإنتدابات', selection=[
        ('draft', 'Draft'),
        ('employee_request', 'Apply Request'),
        ('approved_by_direct_manger', 'Approved Direct Manager'),
        ('approved_by_academic_adviser', 'Approved Academic Adviser'),
        ('admin_financial_manager1', 'Confirm administrative and Financial Manger'),
        ('approved_by_hr', 'Confirmed HR'),
        ('issue_ticket', 'Issue Ticket'),
        ('end_task', 'End Task'),
        ('approve_end_task', 'Confirm End Task'),
        ('accountant', 'confirm Accountant'),
        ('financial_auditor', 'Confirm Financial Auditor'),
        ('financial_manager', 'Confirm Financial Manager'),
        ('financial_monitor', 'Confirm Financial Monitor'),
        ('admin_financial_manager', 'اعتماد المشرف على الادارة العامة للشئون الادارية و المالية'),
        ('general_director_approve', 'General director approve'),
        ('mandat_amount_paid', 'Paid'),
        ('cancel', 'Cancel')], tracking=True, translate=True)

    # المراحل الاساسة للاجازات
    holidays_state = fields.Selection(string='المراحل الاساسة للاجازات', selection=[
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'تم تقديم الطلب'),
        ('medical_manager', 'تمت موافقة المدير الطبي للجامعة'),
        ('direct_manager_approve', 'تمت موافقة المدير المباشر'),
        ('dept_manager_approve', 'تمت موافقة مدير /معتمد الإدارة'),
        ('academic_manager_approve', 'تمت موافقة الوكيل  للشؤون الأكادمية'),
        ('hr_checker', 'تمت موافقة مدقق الموارد البشرية'),
        ('validate1', 'Second Approval'),
        ('validate', 'مدير إدارة الموارد البشرية'),
        ('refuse', 'تم الرفض')], tracking=True, translate=True)

    employee_ids = fields.Many2many("hr.employee", "employees_stages", "stage_id", "employee_id", string="User", translate=True)
    department_ids = fields.Many2many("hr.department", string="Department", translate=True)
    group_ids = fields.Many2many("res.groups", string="Group", translate=True)
    field_ids = fields.Many2many("dynamic.workflow.fields.permission", string="fields", translate=True)
    stage_category = fields.Selection(
        [("principal", "رئيسية"), ("secondary", "فرعية")], required=True, tracking=True
    , translate=True)
    secondary_stage_ids = fields.One2many(
        "dynamic.workflow.stage", "principal_stage_id", string="Secondary stages", tracking=True
    , translate=True)
    principal_stage_id = fields.Many2one("dynamic.workflow.stage", string="Principal stage", tracking=True)
    designation = fields.Boolean("Designation")
    achievement_duration = fields.Integer(string="Achievement Duration (Day(s)")

    send_request_to_direct_manager = fields.Boolean(string='إرسال الطلب للمدير المباشر')
    is_initial_approve_stage = fields.Boolean(string='مرحلة موافقة مبدئية')
    is_return_to_investor_stage = fields.Boolean(string="Return To Draft")
    designation_office = fields.Boolean("Designation Office")
    is_allow_move_other_stage = fields.Boolean("إمكانية الانتقال الى مرحلة اخري")
    parent_id = fields.Many2one("dynamic.workflow.stage", string="المرحلة المنتقل اليها", tracking=True)

    @api.constrains('parent_id')
    def _check_stage_recursion(self):
        if not self._check_recursion():
            raise ValueError(_('Error ! You cannot create recursive Stages.'))

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        for leaf in args:
            if isinstance(leaf, list) and leaf[:-1] == [u"id", u"in"] and isinstance(leaf[2], str):
                leaf[2] = ast.literal_eval(args[2][2])
        return super(DynamicWorkflowStage, self).search(args, offset, limit, order, count)


    @api.depends("stage_type")
    def onchange_stage_type_first(self):
        for rec in self:
            if rec.stage_type == "is_first":
                rec.is_first_type = True
            else:
                rec.is_first_type = False


    @api.depends("stage_type")
    def onchange_stage_type_success(self):
        for rec in self:
            if rec.stage_type == "is_success":
                rec.is_success_type = True
            else:
                rec.is_success_type = False


    @api.depends("stage_type")
    def onchange_stage_type_cancel(self):
        for rec in self:
            if rec.stage_type == "is_cancel":
                rec.is_cancel_type = True
            else:
                rec.is_cancel_type = False


    @api.depends("stage_type")
    def onchange_stage_type_refuse(self):
        for rec in self:
            if rec.stage_type == "is_refuse":
                rec.is_refuse_type = True
            else:
                rec.is_refuse_type = False

class DynamicWorkflowFieldsPermission(models.Model):
    _name = "dynamic.workflow.fields.permission"
    _description = "Dynamic Workflow Fields Permission"
    _inherit = 'mail.thread'

    name = fields.Char(related="field_id.name", tracking=True)
    field_permission = fields.Selection(
        [("read", "Read"), ("write", "Write")], string="Permission", tracking=True
    )
    project_type_ids = fields.Many2many("workflow.project.type", string="Project type", tracking=True)
    field_id = fields.Many2one("ir.model.fields", string="fields")
    is_required = fields.Boolean("Required")
