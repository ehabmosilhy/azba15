# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare, float_is_zero

class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': from_date.strftime('%B %Y'),
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

        if not self.employee_ids:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']

        contracts = self.employee_ids._get_contracts(payslip_run.date_start, payslip_run.date_end, states=['open', 'close'])
        contracts._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end),
            ('date_stop', '>=', payslip_run.date_start),
            ('employee_id', 'in', self.employee_ids.ids),
        ])
        self._check_undefined_slots(work_entries, payslip_run)

        validated = work_entries.action_validate()
        if not validated:
            raise UserError(_("Some work entries could not be validated."))

        default_values = Payslip.default_get(Payslip.fields_get())
        for contract in contracts:
            values = dict(default_values, **{
                'employee_id': contract.employee_id.id,
                'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            })
            payslip = self.env['hr.payslip'].new(values)
            payslip._onchange_employee()
            values = payslip._convert_to_write(payslip._cache)
            payslips += Payslip.create(values)
        payslips.compute_sheet()
        payslip_run.state = 'waiting_approval_1'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    advice_id = fields.Many2one('hr.payroll.advice', string='Bank Advice', copy=False)
    bank_id = fields.Many2one('res.bank', string='Bank', related='employee_id.bank_account_id.bank_id', store=True, )
    payment_type = fields.Selection([('bank', 'Bank'), ('Cash', 'Cash')], related='employee_id.payment_type',
                                    string="Payment Type")


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'
    #
    account_debit_total = fields.Many2one('account.account', string='Total Debit Account',
                                          domain=[('deprecated', '=', False)])
    account_credit_total = fields.Many2one('account.account', string='Total Credit Account',
                                           domain=[('deprecated', '=', False)])

    advance_account_debit_total = fields.Many2one('account.account', string='Total Advance Debit Account',
                                          domain=[('deprecated', '=', False)])
    advance_account_credit_total = fields.Many2one('account.account', string='Total Advance Credit Account',
                                           domain=[('deprecated', '=', False)])
    is_net = fields.Boolean(string='Is Net Salary?', )
    is_export_excel = fields.Boolean(string='تصدير بملف اكسل', )


class Hrpayslipline(models.Model):
    _inherit = 'hr.payslip.line'
    # add related filed with hr.salary.rule stor = true
    is_net = fields.Boolean(string='Is Net Salary?', related='salary_rule_id.is_net')
    is_export_excel = fields.Boolean(string='Is Export Excel?', related='salary_rule_id.is_export_excel')


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['mail.thread', 'hr.payslip.run']


    total_salary_ids = fields.One2many('hr.payslip.run.total', 'payslip_run_id', string="s")
    advice_ids = fields.One2many('hr.payroll.advice', 'batch_id', string='Bank Advice', copy=False)
    is_advance_salary = fields.Boolean(string='Is Advance Salary?',)

    # bank_ids = fields.Many2many("res.bank", string="Banks", store=True,
    # 							default=lambda self: self.env.user.company_id.bank_ids)


    def _compute_advices_count(self):
        """This compute the advice amount and total advices count of an employee.
            """
        self.advice_count = self.env['hr.payroll.advice'].search_count([('batch_id', '=', self.id)])

    advice_count = fields.Integer(string="advice Count", compute='_compute_advices_count')

    journal_total_id = fields.Many2one('account.journal', string='Journal Types', required=False,
                                       default=lambda self: self.env.user.company_id.journal_total_id)
    advance_journal_total_id = fields.Many2one('account.journal', string='Journal Type', required=False,
                                       default=lambda self: self.env.user.company_id.advance_journal_total_id)
    move_id = fields.Many2one('account.move', string="قيد اليومية", readonly=True)
    # state = fields.Selection(selection_add=[
    #     ('draft', 'Draft'),
    #     ('waiting_approval_1', 'اعداد الموارد البشرية'),
    #     ('waiting_approval_2', 'تدقيق الموارد البشرية'),
    #     ('waiting_approval_3', ' اعتماد مختص الحسابات'),
    #     ('waiting_approval_4', ' اعتماد المدقق المالي'),
    #     ('waiting_approval_5', ' اعتماد المدير المالي'),
    #     ('waiting_approval_6', 'اعتماد المراقب المالي '),
    #     ('waiting_approval_7', ' اعتماد مدير الشؤون المالية و الإدارية '),
    #     ('general_director_approve', 'General director approve'),
    #     ('close', 'تم الصرف '),
    # ], string='Status', index=True, readonly=True, copy=False, default='draft',tracking=True)
    state = fields.Selection(selection_add=[
        ('draft_prepare', 'أخصائي الموارد البشرية'),
        ('waiting_approval_1', 'مدراء الوحدات الإدارية'),
        ('waiting_approval_2', 'مدير إدارة الخدمات المساندة'),
        ('waiting_approval_3', ' اعتماد قائد المكتب'),
        ('close', 'تم الإعتماد '),
    ], string='Status', index=True, readonly=True, copy=False, default='draft_prepare',tracking=True)
    require_general_director_approve = fields.Boolean(string='يحتاج موافقة الرئيس',
                                                      compute='_compute_is_exceed_max_amount')

    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id)


    @api.depends('total_salary_ids')
    def _compute_is_exceed_max_amount(self):
        for record in self:
            total_amount = self.env['hr.payslip.run.total'].search(
                [('payslip_run_id', '=', record.id), ('rule_id.is_net', '=', True)],
                limit=1).amount
            if total_amount:

                if total_amount <= record.company_id.max_amount_require_director_approval:
                    record.require_general_director_approve = False
                else:
                    record.require_general_director_approve = True
            else:
                record.require_general_director_approve = False


    def action_waiting_approval_1(self):
        for payslip in self:
            payslip.compute_total_line()
        self.write({'state': 'waiting_approval_1'})


    def recompute_payslips(self):
        for rec in self:
            rec.slip_ids.compute_sheet()


    def action_waiting_approval_2(self):
        self.write({'state': 'waiting_approval_2'})


    def action_waiting_approval_3(self):
        for payslip in self:

            payslip.write({'state': 'waiting_approval_3'})

    def close_payslip_run(self):
        for payslip in self:
            payslip.action_pay()
            payslip.compute_total_line()
            for ll in payslip.slip_ids:
                ll.action_payslip_done()
            # for
            payslip.write({'state': 'close'})
            payslip.generate_advice()
            for dd in payslip.advice_ids:
                dd.compute_advice()

    def action_return_draft(self):
        for record in self:
            if record.move_id:
                record.journal_total_id.update_posted = True
                record.move_id.button_cancel()
                record.move_id.unlink()
            record.write({'state': 'draft_prepare', 'move_id': False})





    # def button_general_director_approve(self):
    #     for payslip in self:
    #         payslip.compute_total_line()
    #         for ll in payslip.slip_ids:
    #             ll.action_payslip_done()
    #         # for
    #         payslip.write({'state': 'general_director_approve'})
    #         payslip.generate_advice()
    #         for dd in payslip.advice_ids:
    #             dd.compute_advice()




    def generate_advice(self):
        list_bank = []
        # bank_ids = self.env['res.bank'].search([])

        # for bank in bank_ids:
        # 	# for line in payslip.advice_line:
        # 	banks = (0,0,{
        # 		'name': self.name + "  " + bank.name,
        # 		'date': self.date_from,
        # 		'bank_id': bank.id,
        # 		'batch_id': self.id,
        # 	})
        # 	list_bank.append(banks)

        self.advice_ids.unlink()

        cash = (0, 0, {
            'name': self.name + "   Cash Payment",
            'date': fields.Date.today() or self.date_start,
            'payment_type': 'cash',
            'batch_id': self.id,
            'journal_id': self.env.user.company_id.journal_cash_id.id,
            'treasury_account_id': self.env.user.company_id.journal_cash_id.default_account_id.id,
            'emp_account_id': self.env.user.company_id.advance_emp_account_id.id if self.is_advance_salary else self.env.user.company_id.emp_account_id.id,
        })
        list_bank.append(cash)
        banks = (0, 0, {
            'name': self.name + "  bank payment",
            'date': fields.Date.today() or self.date_start,
            'payment_type': 'bank',
            'batch_id': self.id,
            'journal_id': self.env.user.company_id.journal_bank_id.id,
            'treasury_account_id': self.env.user.company_id.journal_bank_id.default_account_id.id,
            'emp_account_id': self.env.user.company_id.advance_emp_account_id.id if self.is_advance_salary else self.env.user.company_id.emp_account_id.id,
            'bank_id': self.env.user.company_id.journal_bank_id.bank_id.id,
        })
        list_bank.append(banks)
        self.write({'advice_ids': list_bank})


    def compute_total_line(self):

        rule_ids = self.env['hr.salary.rule'].search([])
        for payslip in self:
            # bonus_line.search([('payslip_run_id','=',self.id)]).unlink()
            payslip.total_salary_ids.unlink()
            total_ids = []
            for re in rule_ids:
                MOTDED_total = 0.0
                for split in self.env['hr.payslip.line'].search(
                        [('salary_rule_id', '=', re.id), ('slip_id.payslip_run_id', '=', payslip.id)]):
                    MOTDED_total += split.total
                if MOTDED_total != 0.0:
                    adjust_debit = (0, 0, {
                        'payslip_run_id': payslip.id,
                        'rule_id': re.id,
                        'amount': MOTDED_total,
                    })
                    total_ids.append(adjust_debit)

            payslip.write({'total_salary_ids': total_ids})

        return True


    def action_pay(self):
        """This create account move for request.
            """
        precision = self.env['decimal.precision'].precision_get('Payroll')
        amount_ids = []
        credit_note = False
        if self.is_advance_salary:
            if not self.advance_journal_total_id:
                raise UserError(_('يجب تحديد حساب الموظف وقيد اليومية للصرف '))
        else:
            if not self.journal_total_id:
                raise UserError(_('يجب تحديد حساب الموظف وقيد اليومية للصرف '))
        if not self.total_salary_ids:
            raise UserError(_('You must compute line Request before Approved.'))

        timenow = time.strftime('%Y-%m-%d')
        for line in self:
            name = line.name
            reference = line.name
            if line.is_advance_salary:
                journal_id = line.advance_journal_total_id
            else:
                journal_id = line.journal_total_id

            amount_ids = []
            debit_sum = credit_sum = 0
            for sa_line in line.total_salary_ids:
                amount = credit_note and -sa_line.amount or sa_line.amount
                if float_is_zero(amount, precision_digits=precision):
                    continue

                if sa_line.rule_id.category_id.code in ['ALW', 'BASIC']:
                    if line.is_advance_salary:
                        debit_account_id = sa_line.rule_id.advance_account_debit_total.id
                    else:
                        debit_account_id = sa_line.rule_id.account_debit_total.id

                    if not debit_account_id:
                        raise UserError(
                            _('The salary rule "%s" has not properly configured the Debit Account!') % (
                                sa_line.rule_id.name))
                    debit_line = (0, 0, {
                        'name': sa_line.rule_id.name + '  for ' + name,
                        'account_id': debit_account_id,
                        'journal_id': journal_id.id,
                        'date': timenow,
                        'debit': amount > 0.0 and amount or 0.0,
                        'credit':  0.0,
                    })
                    amount_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                if sa_line.rule_id.category_id.code == 'DED' or sa_line.rule_id.is_net:
                    if sa_line.rule_id.is_net:
                        if line.is_advance_salary:
                            credit_account_id = self.env.user.company_id.advance_emp_account_id.id
                        else:
                            credit_account_id = self.env.user.company_id.emp_account_id.id

                        if not credit_account_id:
                            raise UserError(
                                _('The payroll account  has not properly configured the general setting!'))
                    else:
                        if line.is_advance_salary:
                            credit_account_id = sa_line.rule_id.advance_account_credit_total.id
                        else:
                            credit_account_id = sa_line.rule_id.account_credit_total.id

                        if not credit_account_id:
                            raise UserError(
                                _('The salary rule "%s" has not properly configured the Credit Account!') % (
                                    sa_line.rule_id.name))

                    credit_line = (0, 0, {
                        'name': sa_line.rule_id.name + '  for ' + name,
                        'account_id': credit_account_id,
                        'journal_id': journal_id.id,
                        'date': timenow,
                        'debit':  0.0,
                        'credit': amount < 0.0 and -amount or amount,
                    })
                    amount_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

            # debit_account_id = line.treasury_account_id.id
            # credit_account_id = line.emp_account_id.id
            # debit_vals = (0, 0, {
            # 	'name': sa_line.rule_id.name + '  for ' +  name,
            # 	'account_id': sa_line.account_id.id,
            # 	'journal_id': journal_id.id,
            # 	'date': timenow,
            # 	'debit': sa_line.debit or 0.0,
            # 	'credit': sa_line.credit or 0.0,
            # 	# 'line_id': line.id,
            # })
            # debit_sum += sa_line.debit
            # credit_sum += sa_line.credit
            # amount_ids.append(debit_line)

            if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                if line.is_advance_salary:
                    acc_id = line.advance_journal_total_id.default_account_id.id
                else:
                    acc_id = line.journal_total_id.default_account_id.id

                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                        line.journal_total_id.name))
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'account_id': acc_id,
                    'journal_id': journal_id.id,
                    'date': timenow,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                amount_ids.append(adjust_credit)

            elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                if line.is_advance_salary:
                    acc_id = line.advance_journal_total_id.default_account_id.id
                else:
                    acc_id = line.journal_total_id.default_account_id.id
                if not acc_id:
                    raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                        line.journal_total_id.name))
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'account_id': acc_id,
                    'journal_id': journal_id.id,
                    'date': timenow,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                amount_ids.append(adjust_debit)

            vals = {
                'narration': name,
                'ref': name,
                'journal_id': journal_id.id,
                'date': timenow,
                'line_ids': amount_ids,
            }
            move = self.env['account.move'].create(vals)
            move.post()

        # self.write({'state': 'paid'})
        self.write({'move_id': move.id})

        return True


class HrPayslipRubTotalSalary(models.Model):
    _name = 'hr.payslip.run.total'
    _description = 'Hr Payslip Run Total'

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Payroll', ondelete="cascade")
    rule_id = fields.Many2one('hr.salary.rule', string='Rule salary ', required=True)
    amount = fields.Float(store=True, default=0.0)

# class MissionsConfiguration(models.Model):
#	 _inherit = 'hr.config.settings'

#	 company_id = fields.Many2one('res.company', string='Company', required=True,
#								  default=lambda self: self.env.user.company_id)
#	 bank_ids = fields.Many2many("res.bank", string="Banks",store= True, related='company_id.bank_ids')


# class ReCompanyConfig(models.Model):
#	 _inherit = 'res.company'

#	 bank_ids = fields.Many2many("res.bank", string="Banks", store=True)
