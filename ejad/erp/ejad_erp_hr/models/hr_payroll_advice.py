import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools import float_compare, float_is_zero

from odoo.addons import decimal_precision as dp


class HrPayrollAdvice(models.Model):
	'''
	Bank Advice
	'''
	_name = 'hr.payroll.advice'
	_description = 'Bank Advice'

	def _get_default_date(self):
		return fields.Date.from_string(fields.Date.today())

	name = fields.Char(readonly=True, required=True,string="الاسم",states={'draft': [('readonly', False)]})
	note = fields.Text(string='ملاحظة',)
	date = fields.Date(readonly=True, required=True, states={'draft': [('readonly', False)]}, default=_get_default_date,
		help='Advice Date is used to search Payslips',string='التاريخ')
	state = fields.Selection([
		('draft', 'مسودة'),
		('confirm', 'موافقة'),
		('paid', 'مدفوعة'),
		('cancel',' الفاء'),
	],string='الحالة', default='draft', index=True, readonly=True)
	number = fields.Char(string='المرجع', readonly=True)
	line_ids = fields.One2many('hr.payroll.advice.line', 'advice_id', string='راتب الموظف',
		states={'draft': [('readonly', False)]}, readonly=True, copy=True)
	chaque_nos = fields.Char(string='رقم الشيك')
	neft = fields.Boolean(string='NEFT Transaction', help='Check this box if your company use online transfer for salary')
	company_id = fields.Many2one('res.company', string='الشركة', required=True, readonly=True,
		states={'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
	bank_id = fields.Many2one('res.bank', string='البنك', readonly=True, states={'draft': [('readonly', False)]},
		help='Select the Bank from which the salary is going to be paid')
	batch_id = fields.Many2one('hr.payslip.run', string='Batch', readonly=True, states={'draft': [('readonly', False)]})
	journal_id = fields.Many2one('account.journal', string='طريقة الدفع', required=False, domain=[('type', 'in', ('bank', 'cash'))])
	treasury_account_id = fields.Many2one('account.account',related="journal_id.default_account_id", string="حساب طريقة الدفع")
	emp_account_id = fields.Many2one('account.account', string="حساب الاستحقاق")
	move_id = fields.Many2one('account.move', string="قيد اليومية", readonly=True)
	payment_type = fields.Selection([('bank','البنك'),('cash','نقدى')],string="نوع الدفع")
	bank_ref = fields.Char('رقم السند')
	bank_ref_seq = fields.Char('Bank Reference Seq')
	cash_ref_seq = fields.Char('cash Reference Seq')


	def _compute_amount(self):
		total_paid = 0.0
		for line in self:
			for advice in line.line_ids:
				total_paid += advice.amount
			# balance_amount = line.line_amount - total_paid
			self.total_amount = total_paid
	total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_amount')


	def compute_advice(self):
		"""
		Advice - Create Advice lines in Payment Advice and
		compute Advice lines.
		"""


		for advice in self:
			old_lines = self.env['hr.payroll.advice.line'].search([('advice_id', '=', advice.id)])
			if old_lines:
				old_lines.unlink()
			payslips = self.env['hr.payslip'].search([('payslip_run_id', '=', advice.batch_id.id),('payment_type' , '=', advice.payment_type ), ('state', '=', 'done')])
			for slip in payslips:
				# if not slip.employee_id.bank_account_id and not slip.employee_id.bank_account_id.acc_number:
				# 	pass
				# 	# raise UserError(_('Please define bank account for the %s employee') % (slip.employee_id.name,))
				payslip_line = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('is_net', '=', True)], limit=1)
				if payslip_line:
					self.env['hr.payroll.advice.line'].create({
						'advice_id': advice.id,
						'payslip_id': slip.id ,
						'name': slip.employee_id.bank_account_id.acc_number or '',
						'bank_id': slip.employee_id.bank_account_id.bank_id.id or '',
						'employee_id': slip.employee_id.id,
						'amount': payslip_line.total
					})
				# slip.advice_id = advice.id

	def check_bank_cash_ref(self):
		if self.payment_type == 'bank':
			if not self.bank_ref_seq:
				bank_ref_seq = self.env['ir.sequence'].next_by_code('payment.bank.seq')
				self.bank_ref_seq = bank_ref_seq
				self.bank_ref = bank_ref_seq
			else:
				self.bank_ref = self.bank_ref_seq

		elif self.payment_type == 'cash':
			if not self.cash_ref_seq:
				cash_ref_seq = self.env['ir.sequence'].next_by_code('payment.cash.seq')
				self.cash_ref_seq = cash_ref_seq
				self.bank_ref = cash_ref_seq
			else:
				self.bank_ref = self.cash_ref_seq

		else:
			self.bank_ref = self.bank_ref or False


	def confirm_sheet(self):
		"""
		confirm Advice - confirmed Advice after computing Advice Lines..
		"""
		for advice in self:
			if not advice.line_ids:
				raise UserError(_('You can not confirm Payment advice without advice lines.'))
			date = fields.Date.from_string(fields.Date.today())
			advice_year = date.strftime('%m') + '-' + date.strftime('%Y')
			number = self.env['ir.sequence'].next_by_code('payment.advice')
			advice.write({
				'number': 'PAY' + '/' + advice_year + '/' + number,
				'state': 'confirm',
			})
			advice.check_bank_cash_ref()


	def set_to_draft(self):
		"""Resets Advice as draft.
		"""
		self.write({'state': 'draft'})



	def cancel_sheet(self):
		"""Marks Advice as cancelled.
		"""
		self.write({'state': 'cancel'})
	

	def action_pay(self):
		"""This create account move for request.
			"""
		self.check_bank_cash_ref()
		if not self.emp_account_id or not self.treasury_account_id or not self.journal_id:
			raise UserError(_('يجب تحديد حساب الموظف وقيد اليومية للصرق '))
		if not self.line_ids:
			raise UserError(_('You must compute line Request before Approved.'))
		timenow = time.strftime('%Y-%m-%d')
		for line in self:
			amount = line.total_amount
			name = line.name
			reference = line.number
			journal_id = line.journal_id.id
			credit_account_id = line.treasury_account_id.id
			debit_account_id = line.emp_account_id.id
			debit_vals = {
				'name': name,
				'account_id': debit_account_id,
				'journal_id': journal_id,
				'date': timenow,
				'debit': amount > 0.0 and amount or 0.0,
				'credit': amount < 0.0 and -amount or 0.0,
				# 'line_id': line.id,
			}
			credit_vals = {
				'name': name,
				'account_id': credit_account_id,
				'journal_id': journal_id,
				'date': timenow,
				'debit': amount < 0.0 and -amount or 0.0,
				'credit': amount > 0.0 and amount or 0.0,
				# 'line_id': line.id,
			}
			vals = {
				'narration': name,
				'ref': reference,
				'journal_id': journal_id,
				'date': timenow,
				'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
			}
			move = self.env['account.move'].create(vals)
			move.post()

		self.write({'state': 'paid'})
		self.write({'move_id': move.id})
		
		return True




	# @api.onchange('company_id')
	# def _onchange_company_id(self):
	#	 self.bank_id = self.company_id.partner_id.bank_ids and self.company_id.partner_id.bank_ids[0].bank_id.id or False


# class HrPayslipRun(models.Model):
#	 _inherit = 'hr.payslip.run'
#	 _description = 'Payslip Batches'

#	 available_advice = fields.Boolean(string='Made Payment Advice?',
#										help='If this box is checked which means that Payment Advice exists for current batch',
#										readonly=False, copy=False)

	
#
#	 def draft_payslip_run(self):
#		 super(HrPayslipRun, self).draft_payslip_run()
#		 self.write({'available_advice': False})

#
#	 def create_advice(self):
#		 for run in self:
#			 if run.available_advice:
#				 raise UserError(_("Payment advice already exists for %s, 'Set to Draft' to create a new advice.") % (run.name,))
#			 company = self.env.user.company_id
#			 advice = self.env['hr.payroll.advice'].create({
#						 'batch_id': run.id,
#						 'company_id': company.id,
#						 'name': run.name,
#						 'date': run.date_end,
#						 'bank_id': company.partner_id.bank_ids and company.partner_id.bank_ids[0].id or False
#					 })
#			 for slip in run.slip_ids:
#				 # TODO is it necessary to interleave the calls ?
#				 slip.action_payslip_done()
#				 if not slip.employee_id.bank_account_id or not slip.employee_id.bank_account_id.acc_number:
#					 raise UserError(_('Please define bank account for the %s employee') % (slip.employee_id.name))
#				 payslip_line = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'NET')], limit=1)
#				 if payslip_line:
#					 self.env['hr.payroll.advice.line'].create({
#						 'advice_id': advice.id,
#						 'name': slip.employee_id.bank_account_id.acc_number,
#						 'ifsc_code': slip.employee_id.bank_account_id.bank_bic or '',
#						 'employee_id': slip.employee_id.id,
#						 'amount': payslip_line.total
#					 })
#		 self.write({'available_advice': True})


class HrPayrollAdviceLine(models.Model):
	'''
	Bank Advice Lines
	'''
	_name = 'hr.payroll.advice.line'
	_description = 'Bank Advice Lines'

	advice_id = fields.Many2one('hr.payroll.advice', string='Bank Advice')
	name = fields.Char('رقم حساب البنك', required=True)
	employee_id = fields.Many2one('hr.employee', string='الموظف', required=True)
	payslip_id = fields.Many2one('hr.payslip', string='كشف الراتب', required=True)
	bank_id = fields.Many2one('res.bank',string='البنك')
	amount = fields.Float(string='بواسطة الراتب', digits=dp.get_precision('Payroll'))
	company_id = fields.Many2one('res.company', related='advice_id.company_id', string='الشركة', store=True)
	ifsc = fields.Boolean(related='advice_id.neft', string='IFSC')

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		self.name = self.employee_id.bank_account_id.acc_number
		self.ifsc_code = self.employee_id.bank_account_id.bank_bic or ''


# class HrPayslip(models.Model):
#	 '''
#	 Employee Pay Slip
#	 '''
#	 _inherit = 'hr.payslip'
#	 _description = 'Pay Slips'

#	 advice_id = fields.Many2one('hr.payroll.advice', string='Bank Advice', copy=False)