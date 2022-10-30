# -*- coding: utf-8 -*-
import time
from datetime import datetime, timedelta
from dateutil import relativedelta

import babel

from odoo import api, fields, models, tools, _
from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from odoo.addons import decimal_precision as dp

# class HrPayslip(models.Model):

# 	_inherit = 'hr.payslip'


# 	@api.model
# 	def get_inputs(self, contract_ids, date_from, date_to):
# 		res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
# 		extra_obj = self.env['hr.deductions']
# 		type_ids = self.env['hr.deductions.type'].search([('id','!=',-1)])
# 		contracts_ids = self.env['hr.contract'].browse(contract_ids)
# 		for c in contracts_ids:
# 			for types  in type_ids:
# 				amount = 0.0
# 				for extra in extra_obj.search([('type_id','=',types.id),('employee_id', '=', c.employee_id.id),('date_deducted', '<=', date_to),('date_deducted','>=', date_from),('state','=','done')]):
# 					amount += extra.de_amount

# 				res.append({
# 					'name': types.name ,
# 					'code': types.rule_id.code,
# 					'contract_id': c.id,
# 					'amount': amount ,
# 				})

# 		return res

class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2many('hr.loan.line', string=" اقصاد القرض")


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'documents.mixin', 'mail.thread']

    state = fields.Selection(tracking=True)
    loan_ids = fields.One2many('hr.loan.line', 'payslip_id', string="Loans")
    emp_no = fields.Integer(related='employee_id.emp_attendance_no',string='رقم الموظف', readonly=True)
    employee_grade_level_id = fields.Many2one(related='contract_id.grade_level_id' ,readonly=True,string="الدرجة الوظيفية")

    # YTI TODO To rename. This method is not really an onchange, as it is not in any view
    # employee_id and contract_id could be browse records

    def onchange_employee_id(self, date_from, date_to, employee_id=False, contract_id=False):
        #defaults
        res = {
            'value': {
                'line_ids': [],
                #delete old input lines
                'input_line_ids': [(2, x,) for x in self.input_line_ids.ids],
                #delete old worked days lines
                'worked_days_line_ids': [(2, x,) for x in self.worked_days_line_ids.ids],
                #'details_by_salary_head':[], TODO put me back
                'name': '',
                'contract_id': False,
                'struct_id': False,
            }
        }
        if (not employee_id) or (not date_from) or (not date_to):
            return res
        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_to, "%Y-%m-%d")))
        employee = self.env['hr.employee'].browse(employee_id)
        locale = 'ar_SA' or 'en_US'
        res['value'].update({
            'name': _('Salary Slip of %s for %s') % (employee.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),
            'company_id': employee.company_id.id,
        })

        if not self.env.context.get('contract'):
            #fill with the first contract of the employee
            contract_ids = self.get_contract(employee, date_from, date_to)
        else:
            if contract_id:
                #set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
            else:
                #if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(employee, date_from, date_to)

        if not contract_ids:
            return res
        contract = self.env['hr.contract'].browse(contract_ids[0])
        res['value'].update({
            'contract_id': contract.id
        })
        struct = contract.struct_id
        if not struct:
            return res
        res['value'].update({
            'struct_id': struct.id,
        })
        #computation of the salary input
        contracts = self.env['hr.contract'].browse(contract_ids)
        worked_days_line_ids = self.get_worked_day_lines(contracts, date_from, date_to)
        input_line_ids = self.get_inputs(contracts, date_from, date_to)
        res['value'].update({
            'worked_days_line_ids': worked_days_line_ids,
            'input_line_ids': input_line_ids,
        })
        return res

    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to
        array = []
        ##########
        lon_obj = self.env['hr.loan'].search([('employee_id', '=', employee.id),('state', '=', 'approve')])
        for loan in lon_obj:
                for loan_line in loan.loan_lines:
                    if date_from <= loan_line.date <= date_to and not loan_line.paid:
                        array.append(loan_line.id)
        self.loan_ids = array
        ############################
        self.company_id = employee.company_id
        if not self.contract_id or self.employee_id != self.contract_id.employee_id:  # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id

        payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        self.name = '%s - %s - %s' % (
        payslip_name, self.employee_id.name or '', format_date(self.env, self.date_from, date_format="MMMM y"))

        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _(
                "This payslip can be erroneous! Work entries may not be generated for the period from %s to %s." %
                (date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1), date_to))
        else:
            self.warning_message = False

        self.worked_days_line_ids = self._get_new_worked_days_lines()
        self.input_line_ids = self._get_new_input_lines(self.contract_id, date_from, date_to)

    def _get_new_input_lines(self, contract, date_from, date_to):
            input_line_values = self._get_input_lines(contract, date_from, date_to)
            input_lines = self.input_line_ids.browse([])
            for i in input_line_values:
                input_lines |= input_lines.new(i)
            return input_lines
        # else:
        #     return [(5, False, False)]

    def _get_input_lines(self, contract, date_from, date_to):
        input_line = []
        extra_obj = self.env['hr.deductions']
        type_ids = self.env['hr.deductions.type'].search([('id','!=',-1)])

        contract_obj = self.env['hr.contract']
        emp_id = contract_obj.browse(contract.id).employee_id
        for loan_type_id in self.env['hr.loans.type'].search([('id','!=',-1)]) :
            lon_obj = self.env['hr.loan'].search([('employee_id', '=', emp_id.id), ('loan_type_id','=',loan_type_id.id),('state', '=', 'approve')])
            loan_amount=0.0
            loan_lines_ids = []
            for loan in lon_obj:
                for loan_line in loan.loan_lines:
                    if date_from <= loan_line.date <= date_to and not loan_line.paid:
                        loan_amount += loan_line.amount
                        loan_lines_ids.append(loan_line.id)

            if loan_amount == 0:
                continue

            input_type_id = self.env['hr.payslip.input.type'].search([('name', '=', loan_type_id.name)], limit=1)

            if not input_type_id:
                input_type_id = self.env['hr.payslip.input.type'].create(
                    {
                'name': loan_type_id.name,
                'code': loan_type_id.rule_id.code})

            input_line.append({
                'input_type_id': input_type_id.id,
                'amount': loan_amount,
                'payslip_id': self.id,
                'contract_id': contract.id,
                'loan_line_id': [(6, 0, loan_lines_ids)],
            })
        for types in type_ids:
            amount = 0.
            for extra in extra_obj.search([('type_id','=',types.id),('employee_id', '=', emp_id.id),('date_deducted', '<=', date_to),('date_deducted','>=', date_from),('state','=','done')]):
                amount += extra.de_amount
            if amount == 0:
                continue

            input_type_id = self.env['hr.payslip.input.type'].search([('name', '=', types.name)], limit=1)

            if not input_type_id:
                input_type_id = self.env['hr.payslip.input.type'].create(
                    {
                'name': types.name,
                'code': types.rule_id.code})

            input_line.append({
                'input_type_id': input_type_id.id,
                'amount': amount,
                'payslip_id': self.id,
                'contract_id': contract.id,
            })

        return input_line


    def action_payslip_done(self):
        for line in self.input_line_ids:
            for lo in  line.loan_line_id:
                lo.paid = True
        return super(HrPayslip, self).action_payslip_done()


   #
   #  def action_payslip_done(self):
   #      for line in self.input_line_ids:
   #          if line.loan_line_id:
   #              line.loan_line_id.action_paid_amount()
   #      return super(HrPayslipAcc, self).action_payslip_done()