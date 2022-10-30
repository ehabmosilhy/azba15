# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
def convert_date_to_dayinweek(date):
    formatted_date = datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
    day_in_week = formatted_date.strftime("%A")
    return day_in_week


class EmployeeMandateMulti(models.Model):
    _name = 'hr.mandate.multi'
    _description = 'Mandate Multi Countries'
    _inherit = ['mail.thread']

    # 
    # def unlink(self):
    #     for rec in self:
    #         rec.parent_id.unlink_onchange_mandate_type(rec.parent_id.employee_id, rec.parent_id.is_multi_mandate, rec.parent_id.type1, rec.parent_id.mandate_line_ids)
    #     return super(EmployeeMandateMulti, self).unlink()

    parent_id = fields.Many2one('hr.mandate.request', string='Parent')
    employee_id = fields.Many2one('hr.employee',related='parent_id.employee_id', string='Employee', tracking=True)
    type_id = fields.Many2one('hr.mandate.type', string='Mandate Type IDs', required=True, tracking=True)
    type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string='Mandate Type', tracking=True)
    saudi_cities_id = fields.Many2one('saudi.city', 'Mandate City',
                                      domain=[('mandate_type_id', '!=', False)], tracking=True)
    countries_id = fields.Many2one('res.country', 'Mandate Country', tracking=True)

    number_days_before = fields.Integer('Days Before Mandate', tracking=True)
    number_days_after = fields.Integer('Days After Mandate', tracking=True)
    number_days = fields.Integer('Mandate Days', tracking=True)

    date_from = fields.Date('Start Date', required=True, tracking=True)
    date_to = fields.Date('End Date', required=True, tracking=True)
    state = fields.Selection(related='parent_id.state', tracking=True)
    description = fields.Text('Description')

    
    @api.onchange('type_id')
    def onchange_type_id_delete_data(self):
        for rec in self:
            rec.saudi_cities_id = False
            rec.countries_id = False

    
    @api.onchange('type_id', 'employee_id')
    def _onchange_mandate_type(self):
        for record in self:
            record.number_days_before = record.type_id.number_days_before
            record.number_days_after = record.type_id.number_days_after
            #record.number_days = record.type_id.number_days
            # employee_grade = record.employee_id.contract_id.grade_level_id
            # if record.type_id.type == 'internal':
            #     record.mandate_amount = employee_grade.internal_mandate
            # elif record.type_id.type == 'external':
            #     record.mandate_amount = employee_grade.external_mandate

    
    @api.onchange('date_from', 'date_to','is_multi_mandate')
    def _onchange_number_days(self):
        for rec in self:
            if rec.date_from and rec.date_to and (rec.date_to >= rec.date_from):
                d1 = datetime.strptime(str(rec.date_from), '%Y-%m-%d')
                d2 = datetime.strptime(str(rec.date_to), '%Y-%m-%d')
                rec.number_days = ((d2 - d1).days) + 1
            else:
                rec.number_days = 0

class EmployeeMandateRequest(models.Model):
    _name = 'hr.mandate.request'
    _description = 'Employee Mandate Request'
    _inherit = ['mail.thread']

    # 
    # def write(self, vals):
    #     # record = super(EmployeeMandateRequest, self).write(vals)
    #     for rec in self:
    #         rec.unlink_onchange_mandate_type(rec.employee_id, rec.is_multi_mandate,
    #                                                    rec.type1, rec.mandate_line_ids)
    #     return super(EmployeeMandateRequest, self).write(vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(EmployeeMandateRequest, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                                  submenu=submenu)
        doc = etree.XML(res['arch'])
        nodes = doc.xpath("//field[@name='employee_id']")
        for node in nodes:
            if self.env.user.has_group('ejad_erp_hr.access_all_employee'):
                node.set('domain', str([('id', '!=', -1)]))
            elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
                node.set('domain', str(['|', ('parent_id.user_id', '=', self.env.user.id), ('department_id', 'child_of',
                                                                                            self.env.user.employee_ids and
                                                                                            self.env.user.employee_ids[
                                                                                                0].department_id.id or [])]))
            elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
                node.set('domain',
                         str(['|', ('parent_id.user_id', '=', self.env.user.id), ('user_id', '=', self.env.user.id)]))
            elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
                node.set('domain', str([('user_id', '=', self.env.user.id)]))
            else:
                node.set('domain', str([('id', '=', -1)]))
        res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group(
                'ejad_erp_hr.access_all_mandates'):
            domain += [('id', '!=', -1)]
        elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
            domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                       ('employee_id.department_id', 'child_of',
                        self.env.user.employee_ids and
                        self.env.user.employee_ids[
                            0].department_id.id or [])]
        elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
            domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                       ('employee_id.user_id', '=', self.env.user.id)]
        elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
            domain += [('employee_id.user_id', '=', self.env.user.id)]
        else:
            domain += [('id', '=', -1)]
        res = super(EmployeeMandateRequest, self).search(domain, offset=offset, limit=limit, order=order, count=count)
        return res

    
    @api.onchange('is_multi_mandate')
    def onchange_is_multi_mandate(self):
        for rec in self:
            rec.type_id = False
            rec.saudi_cities_id = False
            rec.countries_id = False
            rec.mandate_line_ids = False
            rec.date_from = False
            rec.date_to = False
            rec.number_days_before = False
            rec.number_days_after= False
            rec.number_days = False


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group(
                'ejad_erp_hr.access_all_mandates'):
            domain += [('id', '!=', -1)]
        elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
            domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                       ('employee_id.department_id', 'child_of',
                        self.env.user.employee_ids and
                        self.env.user.employee_ids[
                            0].department_id.id or [])]
        elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
            domain += ['|', ('employee_id.parent_id.user_id', '=', self.env.user.id),
                       ('employee_id.user_id', '=', self.env.user.id)]
        elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
            domain += [('employee_id.user_id', '=', self.env.user.id)]
        else:
            domain += [('id', '=', -1)]
        res = super(EmployeeMandateRequest, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res

    @api.model
    def default_get_employee(self):
        result = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return result and result[0] or False

    
    @api.onchange('type_id', 'employee_id', 'is_multi_mandate','type1','mandate_line_ids')
    def _onchange_mandate_type(self):
        for record in self:
            if not record.is_multi_mandate:
                record.number_days_before = record.type_id.number_days_before
                record.number_days_after = record.type_id.number_days_after
                #record.number_days = record.type_id.number_days
                employee_grade = record.employee_id.contract_id.grade_level_id
                if record.type_id.type == 'internal':
                    record.mandate_amount = employee_grade.internal_mandate
                elif record.type_id.type == 'external':
                    record.mandate_amount = employee_grade.external_mandate
            else:
                record.number_days_before = max([line.number_days_before for line in record.mandate_line_ids]) if record.mandate_line_ids else False
                record.number_days_after = max([line.number_days_after for line in record.mandate_line_ids]) if record.mandate_line_ids else False
                record.date_from = min([line.date_from for line in record.mandate_line_ids]) if record.mandate_line_ids else False
                record.date_to = max([line.date_to for line in record.mandate_line_ids]) if record.mandate_line_ids else False
                record.number_days = sum([line.number_days or 0 for line in record.mandate_line_ids]) if record.mandate_line_ids else False
                employee_grade = record.employee_id.contract_id.grade_level_id
                if record.type1 == 'internal':
                    record.mandate_amount = employee_grade.internal_mandate
                elif record.type1 == 'external':
                    record.mandate_amount = employee_grade.external_mandate

    def update_days(self):
        for record in self:
            if record.is_multi_mandate:
                record.number_days_before = max(
                    [line.number_days_before for line in record.mandate_line_ids]) if record.mandate_line_ids else False
                record.number_days_after = max(
                    [line.number_days_after for line in record.mandate_line_ids]) if record.mandate_line_ids else False
                record.date_from = min(
                    [line.date_from for line in record.mandate_line_ids]) if record.mandate_line_ids else False
                record.date_to = max(
                    [line.date_to for line in record.mandate_line_ids]) if record.mandate_line_ids else False
                record.number_days = sum(
                    [line.number_days or 0 for line in record.mandate_line_ids]) if record.mandate_line_ids else False
                employee_grade = record.employee_id.contract_id.grade_level_id if record.employee_id else False
                if record.type1 == 'internal' and record.employee_id:
                    record.mandate_amount = employee_grade.internal_mandate
                elif record.type1 == 'external' and record.employee_id:
                    record.mandate_amount = employee_grade.external_mandate

    
    @api.onchange('date_from', 'date_to', 'is_multi_mandate')
    def _onchange_number_days(self):
        for rec in self:
            if not rec.is_multi_mandate:
                if rec.date_from and rec.date_to and (rec.date_to >= rec.date_from):
                    d1 = datetime.strptime(str(rec.date_from), '%Y-%m-%d')
                    d2 = datetime.strptime(str(rec.date_to), '%Y-%m-%d')
                    rec.number_days = ((d2 - d1).days) + 1
                else:
                    rec.number_days = 0

    
    def _compute_manager(self):
        for rec in self:
            rec.manager_id = rec.sudo().employee_id.parent_id.id

    type1 = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
    ], string='Mandate Type1', tracking=True)
    mandate_line_ids = fields.One2many('hr.mandate.multi','parent_id', string="Lines")
    is_multi_mandate = fields.Boolean(string="Is multi Mandate?", tracking=True)
    name = fields.Char('رقم الطلب', readonly=True, tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=default_get_employee, tracking=True)
    department_id = fields.Many2one(related='employee_id.department_id', string='Department', readonly=True, tracking=True)
    job_id = fields.Many2one(related='employee_id.job_id', string='Job', readonly=True, tracking=True)
    # manager_id = fields.Many2one(related='employee_id.parent_id', string='manager', readonly=True, tracking=True)
    manager_id = fields.Many2one('hr.employee',compute='_compute_manager', string='manager')
    contract_type = fields.Selection([('sicetific', 'هيئة علمية '),
                                      ('management', 'ادارين'),
                                      ('staff', 'مهنين')], related="employee_id.contract_type", string="نوع العقد", tracking=True)

    type_id = fields.Many2one('hr.mandate.type', string='Mandate Type IDs', required=False, tracking=True)
    type = fields.Selection(related='type_id.type', tracking=True)
    mandate_reason = fields.Many2one('mandate.reason', string='Reason', required=False, tracking=True)
    saudi_cities_id = fields.Many2one('saudi.city', 'Mandate City',
                                      domain=[('mandate_type_id', '!=', False)], tracking=True)
    countries_id = fields.Many2one('res.country', 'Mandate Country', tracking=True)

    number_days_before = fields.Integer('Days Before Mandate', tracking=True)
    number_days_after = fields.Integer('Days After Mandate', tracking=True)
    number_days = fields.Integer('Mandate Days', tracking=True)

    date_from = fields.Date('Start Date', required=True, tracking=True)
    date_to = fields.Date('End Date', required=True, tracking=True)
    mandate_amount = fields.Float(' Mandate Amount', tracking=True)
    total_mandate_amount = fields.Float('اجمالي مبلغ الانتداب', tracking=True)
    attachment_filename = fields.Char(string='اسم المرفق')
    attachment_filename1 = fields.Char(string='اسم المرفق1')
    mandate_attachment = fields.Binary('Mandate Task File', states={'draft': [('required', True)]}, tracking=True)
    end_task_report_attachment = fields.Binary('End Task Report', states={'issue_ticket': [('required', True)]}, tracking=True)
    note = fields.Text('Notes', tracking=True)
    refuse_reason = fields.Text('Refuse Reason', states={'cancel': [('required', True)]}, tracking=True)
    obligations_involved = fields.Text('The Obligations Involved', tracking=True)
    activity_name = fields.Char('Activity Name', tracking=True)
    implementing_agency = fields.Char('The implementing Agency', tracking=True)
    city_name = fields.Char('City Name', tracking=True)
    current_user_employee_manager = fields.Boolean(string='is_manager', compute="_is_current_user_employee_manager",
                                                   )
    current_user_employee = fields.Boolean(string='is_employee', compute="_is_current_user_employee_manager",
                                           )

    move_id = fields.Many2one('account.move', string="قيد اليومية", readonly=True, tracking=True)

    payment_type2 = fields.Selection([('bank', 'تحويل بنكي'), ('check', 'شيك'), ('cash', 'صندوق (نقد)')],
                                     default='bank', string='نوع السداد', tracking=True)
    journal_id = fields.Many2one('account.journal', string="طريق السداد ", domain=[('type', 'in', ('bank', 'cash'))], tracking=True)
    bank_ref = fields.Char('رقم السند', tracking=True)
    bank_check_no = fields.Char('رقم الشيك', tracking=True)
    treasury_account_id = fields.Many2one('account.account', related="journal_id.default_account_id",
                                          string="الحساب الدائن", tracking=True)
    mandate_account_id = fields.Many2one('account.account', related="type_id.account_id",
                                          string="الحساب المدين", tracking=True)

    state = fields.Selection(string='Status', tracking=True, selection=[
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
        ('cancel', 'Cancel')],
                             readonly=True,
                             default='draft')
    state1 = fields.Selection(string='Status1', selection=[
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
        ('admin_financial_manager', 'Confirm administrative and Financial Manger'),
        ('general_director_approve', 'general_director_approve'),
        ('mandat_amount_paid', 'Paid'),
        ('cancel', 'Cancel')], store=True, compute='get_state')
    bank_ref_seq = fields.Char('Bank Reference Seq')
    cash_ref_seq = fields.Char('cash Reference Seq')
    require_general_director_approve = fields.Boolean(string='يحتاج موافقة الرئيس',
                                                      compute='_compute_is_exceed_max_amount')
    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)

    return_reason = fields.Char(string="سبب الإرجاع", tracking=True)
    returned_by = fields.Many2one("res.users", string="Returned by", tracking=True)
    is_returned = fields.Boolean()
    return_message = fields.Text("Refuse message", tracking=True)

    @api.depends('total_mandate_amount')
    def _compute_is_exceed_max_amount(self):
        for record in self:
            if record.total_mandate_amount <= record.company_id.max_amount_require_director_approval:
                record.require_general_director_approve = False
            else:
                record.require_general_director_approve = True

    
    @api.depends('state')
    def get_state(self):
        for rec in self:
            rec.state1 = rec.state

    
    @api.onchange('number_days_before', 'number_days_after', 'number_days', 'mandate_amount')
    def onchange_manadate_amount(self):
        for rec in self:
            rec.total_mandate_amount = (rec.mandate_amount or 0.00) * (
                    (rec.number_days_before or 0.00) + (rec.number_days_after or 0.00) + (rec.number_days or 0.00))

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.mandate.request')
        result = super(EmployeeMandateRequest, self).create(vals)

        return result

    
    def _is_current_user_employee_manager(self):
        for rec in self:
            if rec.env.uid == rec.sudo().employee_id.parent_id.user_id.id \
                    or rec.user_has_groups(
                'ejad_erp_hr.hr_mandate_direct_manager') \
                    or (rec.env.uid == rec.employee_id.user_id.id and rec.user_has_groups(
                'ejad_erp_hr.hr_mandate_employee_itself_direct_manager')):

                rec.current_user_employee_manager = True
            else:
                rec.current_user_employee_manager = False
            if rec.env.uid == rec.employee_id.user_id.id:
                rec.current_user_employee = True
            else:
                rec.current_user_employee = False

    
    def button_employee_send_request(self):
        for record in self:
            # if self.env.user != self.employee_id.user_id and self.env.user != self.manager_id.user_id:
            #     raise UserError('تقديم الطلب يجب أن يكون بواسطة الموظف أو المدير المباشر')
            #
            record.state = 'employee_request'

    
    def button_approved_by_direct_manger(self):
        for record in self:
            # if self.env.user != self.manager_id.user_id:
            #     raise UserError('الموافقة على الطلب يجب أن تكون بواسطة المدير المباشر')

            record.state = 'approved_by_direct_manger'

    
    def button_approved_by_academic_adviser(self):
        for record in self:
            record.state = 'approved_by_academic_adviser'

    
    def button_approved_by_hr(self):
        for record in self:
            record.state = 'approved_by_hr'

    
    def button_issue_ticket(self):
        for record in self:
            record.state = 'issue_ticket'

    
    def button_end_task(self):
        for record in self:
            # if self.env.user != self.employee_id.user_id and self.env.user != self.manager_id.user_id:
            #     raise UserError('إنهاء المهمة يجب أن تكون بواسطة الموظف أو المدير المباشر')

            record.state = 'end_task'

    
    def button_approve_end_task(self):
        for record in self:
            # if self.env.user != self.manager_id.user_id:
            #     raise UserError('إعتماد إنهاء المهمة يجب أن تكون بواسطة المدير المباشر')

            record.state = 'approve_end_task'

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
                self.bank_ref = self.cash_ref_seq

        else:
            self.bank_ref = self.bank_ref or False

    
    def button_accountant(self):
        for record in self:
            record.check_bank_cash_ref()
            record.state = 'accountant'

    
    def button_financial_auditor(self):
        for record in self:
            record.check_bank_cash_ref()
            record.state = 'financial_auditor'
            if not self.journal_id.default_account_id:
                raise UserError(_(
                    "Please fill default credit account fields in the selected journal in order to create journal entery"))

            if not self.type_id.account_id:
                raise UserError(
                    _("Please fill account fields in the selected mandate type in order to create journal entery"))

            move_id = self.env['account.move'].create({
                'journal_id': self.journal_id.id,
                'ref': self.name + ' انتداب  ',
                'date': fields.Date.today(),
                'move_type': 'entry',
                'bank_account_info': self.employee_id.bank_account_id.acc_number,
            })
            aml = self.env['account.move.line'].with_context(check_move_validity=False)
            aml.create({
                'name': self.employee_id.name + "   - بدل انتداب ",
                'account_id': self.type_id.account_id.id,
                'credit': 0,
                'debit': self.total_mandate_amount,
                'move_id': move_id.id

            })
            aml.create({
                'name': self.employee_id.name + "  - بدل انتداب ",
                'account_id': self.journal_id.default_account_id.id,
                'credit': self.total_mandate_amount,
                'debit': 0,
                'move_id': move_id.id

            })
            move_id.post()
            self.move_id = move_id
            self.journal_id = self.journal_id


    
    def button_financial_manager(self):
        for record in self:
            record.check_bank_cash_ref()
            record.state = 'financial_manager'

    
    def button_financial_monitor(self):
        for record in self:
            record.check_bank_cash_ref()
            record.state = 'financial_monitor'

    
    def button_admin_financial_manager(self):
        for record in self:
            record.check_bank_cash_ref()
            record.state = 'admin_financial_manager'

    
    def button_admin_financial_manager1(self):
        for record in self:
            record.check_bank_cash_ref()
            record.state = 'admin_financial_manager1'

    
    def button_general_director_approve(self):
        for record in self:
            record.check_bank_cash_ref()
            record.state = 'general_director_approve'

    
    def button_mandat_amount_paid(self):
        for record in self:
            record.state = 'mandat_amount_paid'

    
    def button_cancel(self):
        for record in self:
            # if self.env.user != self.manager_id.user_id and not self.env.user.has_group(
            #         'ejad_erp_base.group_general_director'):
            #     raise UserError('إلغاء الطلب يجب أن يكون بواسطة المدير المباشر او رئيس الجامعة')
            if not record.refuse_reason:
                raise UserError('يجب ادخال سبب الرفض')
            if record.move_id:
                record.move_id.journal_id.update_posted = True
                record.move_id.button_cancel()
                record.move_id.unlink()
            record.state = 'cancel'
            record.stage_id = record.stage_ids.filtered(lambda r: r.mandate_state == 'cancel').id

    # 
    # def button_set_draft(self):
    #     for record in self:
    #         record.state = 'draft'

    """
        Start workflow fields ( حقول المراحل )
    """
    category = fields.Many2one("dynamic.workflow.category", string="Category", tracking=True,
                               )

    project_type = fields.Many2one("workflow.project.type", string="Project type", tracking=True,
                                   default=lambda self: self.env.ref(
                                       'ejad_erp_hr.mandate_project_type_data').id)
    project_code = fields.Char(related="project_type.code")

    stage_ids = fields.Many2many("dynamic.workflow.stage", compute="_compute_stage_ids", tracking=True,
                                 )
    # stage_id = fields.Many2one("dynamic.workflow.stage", string="المرحلة", tracking=True,
    #                            default=lambda self: self.env.ref('ejad_erp_hr.dynamic_workflow_stage_data_0').id,
    #                            )
    stage_id = fields.Many2one("dynamic.workflow.stage", string="المرحلة", tracking=True)

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
        context = {"previous_stage_ids": previous_stage_ids, "default_mandate_id": self.id}
        context.update(self.env.context)

        return {
            "type": "ir.actions.act_window",
            "name": "Previous Stage",
            "res_model": "dynamic.workflow.mandate.stage.previous.wizard",
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
            rec.stage_ids = rec.project_type.stage_ids.ids

    
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
                    if self.state in ('approve_end_task', 'financial_auditor', 'financial_manager', 'financial_monitor', 'admin_financial_manager'):
                        self.check_bank_cash_ref()
                        self.stage_id = stage_ids[stage]
                        if stage_ids[stage].mandate_state:
                            self.state = stage_ids[stage].mandate_state
                    elif self.state == 'accountant':
                        self.button_financial_auditor()
                        self.stage_id = stage_ids[stage]

                    else:
                        self.stage_id = stage_ids[stage]
                        if stage_ids[stage].mandate_state:
                            self.state = stage_ids[stage].mandate_state

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

# @api.onchange('employee_id', 'type')
# def onchange_employee_id(self):
#     if self.type == 'internal':
#         self.mandate_amount = self.employee_id.job_id.mandate_amount_conf_id.internal_amount
#     elif self.type == 'external':
#         self.mandate_amount = self.employee_id.job_id.mandate_amount_conf_id.external_amount
#     else:
#         self.mandate_amount = 0.0
