# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
import json
from lxml import etree
# from odoo.osv.orm import setup_modifiers



class hr_loans_type(models.Model):
    _name = 'hr.loans.type'
    _description = "نوع القروض"

    name = fields.Char(string="الاسم", required=True)
    rule_id = fields.Many2one('hr.salary.rule', string='Rule salary ', required=True)
    # debit_account_id = fields.Many2one('account.account', string="Debit Account")
    emp_account_id = fields.Many2one('account.account', string="حساب القرض ")
    loan_type = fields.Selection([
        ('long', 'قرض عام  '),
        ('custom', 'قرض الحالات الخاصة '),
    ], string="نوع القرض", default='long')
    loan_percentage = fields.Integer("نسبة القرض من النهاية الخدمة ", default=80)
    loan_amount = fields.Float("قيمة القرض النهائي ", default=15000.0)


class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get_employee(self):
        result = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        return result and result[0] or False


    def _compute_loan_amount(self):
        total_paid = 0.0
        for loan in self:
            for line in loan.loan_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = loan.loan_amount - total_paid
            self.total_amount = loan.loan_amount
            self.balance_amount = balance_amount
            self.total_paid_amount = total_paid

    note = fields.Text(string="ملاحظات", tracking=True,)
    name = fields.Char(string="Ref", default="/", readonly=True)
    date = fields.Date(string="التاريخ", default=fields.Date.context_today, readonly=True)
    employee_id = fields.Many2one('hr.employee', string="الموظف", required=True, default=default_get_employee)
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True,
                                    string="القسم")

    installment = fields.Integer(string="عدد الاستقطاعات ", default=1)
    payment_date = fields.Date(string="بدء الاستقطاع من تاريخ ", required=True, default=fields.Date.context_today)
    loan_lines = fields.One2many('hr.loan.line', 'loan_id', string="الاستقطاعات ", index=True)
    # emp_account_id = fields.Many2one('account.account', string="حساب القروض ")
    # treasury_account_id = fields.Many2one('account.account', string="حساب الخزية")
    # journal_id = fields.Many2one('account.journal', string="نوع القيد ")
    loans_count = fields.Integer(string='عدد القزوص', default=0)
    ens_months = fields.Integer(string='اشهر نهاية الخدمة',readonly=False )
    ens_months_c = fields.Integer(string='حساب اشهر نهاية الخدمة', store=True, compute='get_ens_months')
    # wage = fields.Float(string="الراتب الأساسي",related="employee_id.contract_id.wage", readonly=True)
    wage = fields.Float(string="الراتب الأساسي")


    @api.depends('ens_months')
    def get_ens_months(self):
        for rec in self:
            rec.ens_months_c = rec.ens_months or 0

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        result = super(HrLoan, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(result['arch'])
        if self.env.user.has_group('ejad_erp_hr.group_edit_loan_amount'):
            for node in doc.xpath("//field[@name='loan_amount']"):
                node.set('readonly', '0')
                # setup_modifiers(node, result['fields']['loan_amount'])
                modifiers = json.loads(node.get("modifiers"))
                modifiers["readonly"] = True
                node.set("modifiers", json.dumps(modifiers))
        nodes = doc.xpath("//field[@name='employee_id']")
        for node in nodes:
            if self.env.user.has_group('ejad_erp_hr.access_all_employee'):
                node.set('domain', str([('id', '!=', -1)]))
            #elif self.env.user.has_group('ejad_erp_hr.access_department_employee_only'):
            #    node.set('domain', str(['|', ('parent_id.user_id', '=', self.env.user.id), ('department_id', 'child_of',
            #                                                                                self.env.user.employee_ids and
            #                                                                                self.env.user.employee_ids[
            #                                                                                    0].department_id.id or [])]))
            #elif self.env.user.has_group('ejad_erp_hr.access_direct_employee_manager_only'):
            #    node.set('domain',
            #             str(['|', ('parent_id.user_id', '=', self.env.user.id), ('user_id', '=', self.env.user.id)]))
            elif self.env.user.has_group('ejad_erp_hr.access_general_employee_only'):
                node.set('domain', str([('user_id', '=', self.env.user.id)]))
            else:
                node.set('domain', str([('id', '=', -1)]))
        result['arch'] = etree.tostring(doc)
        return result

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group('ejad_erp_hr.access_all_loans'):
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
        res = super(HrLoan, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return res

    @api.model
    def search(self, domain, offset=0, limit=None, order=None, count=False):
        if self.env.user.has_group('ejad_erp_hr.access_all_employee') or self.env.user.has_group('ejad_erp_hr.access_all_loans'):
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
        res = super(HrLoan, self).search(domain, offset=offset, limit=limit, order=order, count=count)
        return res

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        # self.ens_months= self.employee_id.ens_months
        # salary = self.salary
        today = str(fields.Date.today())
        date_of_join = str(self.employee_id.date_of_join)
        if (self.employee_id) and ((datetime.strptime(today, '%Y-%m-%d') - (
                datetime.strptime(date_of_join, '%Y-%m-%d'))).days / 354) >= 1:
            if (datetime.strptime(date_of_join, '%Y-%m-%d')) < (
            datetime.strptime('1999-01-01', '%Y-%m-%d')):
                benefits = ((datetime.strptime('1999-01-01', '%Y-%m-%d')) - (
                    datetime.strptime(date_of_join, '%Y-%m-%d'))).days / 354 * 2
                benefits += ((datetime.strptime(today, '%Y-%m-%d')) - (
                    datetime.strptime('1999-01-01', '%Y-%m-%d'))).days / 354
                self.ens_months = int(benefits)
            else:
                benefits = ((datetime.strptime(today, '%Y-%m-%d')) - (
                    datetime.strptime(date_of_join, '%Y-%m-%d'))).days / 354
                # print('  ######      ',benefits)
                self.ens_months = int(benefits)
        else:
            self.ens_months = 0

        self.loans_count = self.employee_id.loans_count
        self.wage = self.employee_id.contract_id.wage
        if self.employee_id.loans_count >= 3:
            self.is_other_amount = True
        else:
            self.is_other_amount = False


    @api.depends('employee_id', 'ens_months', 'wage', 'loans_count', 'loan_type_id')
    def _compute_loan_amount_custome(self):
        loan_amount = 0.0
        wage = self.wage
        ens_months = self.ens_months
        percentage = self.loan_type_id.loan_percentage
        amount = self.loan_type_id.loan_amount
        if self.loans_count < 2:
            loan_amount = (wage * percentage / 100) * ens_months
        elif self.loans_count == 2:
            loan_amount = amount
        #if self.loan_amount_other and (self.loan_amount_other > 0):
        #    loan_amount = self.loan_amount_other
        self.loan_amount = loan_amount

    is_other_amount = fields.Boolean(string="تفعيل القرض الخاص", default=False)
    loan_type_id = fields.Many2one("hr.loans.type", "نوع القرض")  # TODO required=True need migration script
    emp_account_id = fields.Many2one('account.account', related="loan_type_id.emp_account_id", string="الحساب المدين")
    journal_id = fields.Many2one('account.journal', string="طريق السداد ", domain=[('type', 'in', ('bank', 'cash'))])

    treasury_account_id = fields.Many2one('account.account', related="journal_id.default_account_id",
                                          string="الحساب الدائن")
    grade_level_id = fields.Many2one(comodel_name='hr.grade.level', tracking=True,
                                     related="employee_id.grade_level_id", readonly=True, string="المرتبة / الدرجة ")
    contract_type = fields.Selection( related="employee_id.contract_type", readonly=True,
                                     string="نوع العقد")

    company_id = fields.Many2one('res.company', 'الشركة', readonly=True,
                                 default=lambda self: self.env.user.company_id,
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='العملة ', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="الوظيفة")
    loan_amount_other = fields.Float(string="مبلغ السلفية الخاصة", default=0.0)
    loan_amount = fields.Float(string="مبلغ السلفية", compute='_compute_loan_amount_custome', store=True,
                               tracking=True)
    total_amount = fields.Float(string="مجموع المبالغ", readonly=True, compute='_compute_loan_amount')
    balance_amount = fields.Float(string="الرصيد", compute='_compute_loan_amount')
    total_paid_amount = fields.Float(string="المبلغ المدفوع", compute='_compute_loan_amount')
    move_id = fields.Many2one('account.move', string="قيد اليومية", readonly=True)
    payment_type2 = fields.Selection([('bank', 'تحويل بنكي'), ('check', 'شيك'), ('cash', 'صندوق (نقد)')],
                                     default='bank', string='نوع السداد')
    bank_ref = fields.Char('رقم السند')
    bank_check_no = fields.Char('رقم الشيك')


    state = fields.Selection([
        ('draft', 'مسودة '),
        ('waiting_approval_1', 'الطلب مقدم'),
        ('waiting_approval_2', 'مؤكد استحقاق الموظف'),
        ('waiting_approval_3', 'اعتماد مسؤول تدقيق المصروفات '),
        ('waiting_approval_4', 'اعتماد مدير الادارة المالية '),
        ('waiting_approval_5', 'اعتماد  المراقب المالي '),
        ('waiting_approval_6', 'اعتماد مدير الشؤون المالية والإدارية '),
        ('general_director_approve', 'موافقةالرئيس'),
        ('approve', 'تم عملية الصرف'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="الحالة", default='draft', tracking=True, copy=False, )
    bank_ref_seq = fields.Char('Bank Reference Seq')
    cash_ref_seq = fields.Char('cash Reference Seq')
    require_general_director_approve = fields.Boolean(string='يحتاج موافقة الرئيس',
                                                      compute='_compute_is_exceed_max_amount')
    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)


    @api.depends('total_amount')
    def _compute_is_exceed_max_amount(self):
        for record in self:
            if record.total_amount <= record.company_id.max_amount_require_director_approval:
                record.require_general_director_approve = False
            else:
                record.require_general_director_approve = True

    @api.model
    def create(self, values):
        # loan_count = self.env['hr.loan'].search_count([('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
        #                                                ('balance_amount', '!=', 0)])
        # if loan_count:
        #     raise UserError(_('The employee has already a pending installment.'))
        # else:
        values['name'] = self.env['ir.sequence'].get('hr.loan.seq') or ' '
        res = super(HrLoan, self).create(values)
        return res


    def action_refuse(self):
        self.write({'state': 'refuse'})
        if self.move_id:
            self.move_id.journal_id.update_posted = True
            self.move_id.button_cancel()
            self.move_id.unlink()


    def action_submit(self):
        self.write({'state': 'waiting_approval_1'})


    def action_waiting_approval_2(self):
        self.write({'state': 'waiting_approval_2'})

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


    def action_waiting_approval_3(self):
        for record in self:
            record.check_bank_cash_ref()
            record.write({'state': 'waiting_approval_3'})
            if not self.loan_lines:
                raise UserError(_('يجب انشاء الاسقطاعات قبل الصرف'))

            if not self.emp_account_id or not self.treasury_account_id or not self.journal_id:
                raise UserError(_('يجب تحديد حساب الموظف وقيد اليومية للصرق '))
            if not self.loan_lines:
                raise UserError(_('You must compute Loan Request before Approved.'))
            timenow = time.strftime('%Y-%m-%d')
            for loan in self:
                amount = loan.loan_amount
                loan_name = loan.employee_id.name
                reference = loan.name
                journal_id = loan.journal_id.id
                debit_account_id = loan.treasury_account_id.id
                credit_account_id = loan.emp_account_id.id
                debit_vals = {
                    'name': 'Loan For' + ' ' + loan_name,
                    'account_id': debit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'credit': amount > 0.0 and amount or 0.0,
                    'debit': amount < 0.0 and -amount or 0.0,
                    # 'loan_id': loan.id,
                }
                credit_vals = {
                    'name': 'Loan For' + ' ' + loan_name,
                    'account_id': credit_account_id,
                    'journal_id': journal_id,
                    'date': timenow,
                    'credit': amount < 0.0 and -amount or 0.0,
                    'debit': amount > 0.0 and amount or 0.0,
                    # 'loan_id': loan.id,
                }
                vals = {
                    'narration': 'Loan For' + ' ' + loan_name,
                    'ref': reference,
                    'journal_id': journal_id,
                    'date': timenow,
                    'bank_account_info': loan.employee_id.bank_account_id.acc_number,
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                move = self.env['account.move'].create(vals)
                move.post()
            # self.employee_id.loans_count = self.employee_id.loans_count + 1
            self.write({'move_id': move.id})


    def action_waiting_approval_4(self):
        self.check_bank_cash_ref()
        self.write({'state': 'waiting_approval_4'})


    def action_waiting_approval_5(self):
        self.check_bank_cash_ref()
        self.write({'state': 'waiting_approval_5'})


    def action_waiting_approval_6(self):
        self.write({'state': 'waiting_approval_6'})
        self.check_bank_cash_ref()
        self.employee_id.loans_count = (self.employee_id.loans_count or 0) + 1


    def action_cancel(self):
        self.write({'state': 'cancel'})

    #
    # def action_approve(self):
    #     for data in self:
    #         contract_obj = self.env['hr.contract'].search([('employee_id', '=', data.employee_id.id),
    #                                                        ('state', '=', 'open')], limit=1)
    #         if not contract_obj:
    #             raise UserError(_('You must Define a contract for employee.'))
    #         if not data.loan_lines:
    #             raise UserError(_('Please Compute installment.'))
    #         else:
    #             self.write({'state': 'approve'})


    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'لايمكن حزف الستقطاع الا في حالة الغاء')
        return super(HrLoan, self).unlink()


    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for loan in self:
            loan.loan_lines.unlink()
            date_start = datetime.strptime(str(loan.payment_date), '%Y-%m-%d')
            amount = loan.loan_amount / loan.installment
            for i in range(1, loan.installment + 1):
                self.env['hr.loan.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': loan.employee_id.id,
                    'loan_id': loan.id})
                date_start = date_start + relativedelta(months=1)
        return True


    def button_general_director_approve(self):
        for record in self:
            record.check_bank_cash_ref()
            record.state = 'general_director_approve'



    def action_approve(self):
        """This create account move for request.
            """
        # loan_approve = self.env['ir.config_parameter'].sudo().get_param('account.loan_approve')
        contract_obj = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id),
                                                       ('state', '=', 'open')], limit=1)
        # if not contract_obj:
        #     raise UserError(_('يجب تعريف عقد للموظف'))

        self.write({'state': 'approve'})


        return True


class InstallmentLine(models.Model):
    _name = "hr.loan.line"
    _description = "Installment Line"

    date = fields.Date(string="تاريخ الاستقطاع ", required=True)
    employee_id = fields.Many2one('hr.employee', string="الموظف")
    amount = fields.Float(string="المبلغ", required=True)
    paid = fields.Boolean(string="مدفوع")
    loan_id = fields.Many2one('hr.loan', string="القرض.")
    payslip_id = fields.Many2one('hr.payslip', string="قسيمة المرتب .")


    def action_paid_amount(self):
        """This create the account move line for payment of each installment.
            """
        timenow = time.strftime('%Y-%m-%d')
        for line in self:
            if line.loan_id.state != 'approve':
                raise UserError(_('Loan Request must be approved'))
            amount = line.amount
            loan_name = line.employee_id.name
            reference = line.loan_id.name
            journal_id = line.loan_id.journal_id.id
            debit_account_id = line.loan_id.emp_account_id.id
            credit_account_id = line.loan_id.treasury_account_id.id
            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,
            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': timenow,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
            }
            vals = {
                'name': 'Loan For' + ' ' + loan_name,
                'narration': loan_name,
                'ref': reference,
                'journal_id': journal_id,
                'date': timenow,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.post()
        #self.employee_id.loans_count = self.loans_count + 1

        return True


class HrEmployee(models.Model):
    _inherit = "hr.employee"


    def _compute_employee_loans(self):
        """This compute the loan amount and total loans count of an employee.
            """
        self.loan_count = self.env['hr.loan'].search_count([('employee_id', '=', self.id)])

    loan_count = fields.Integer(string="Loan Count", compute='_compute_employee_loans')
