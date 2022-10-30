# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class HrLoan(models.Model):
    _inherit = 'hr.employee'
    indemnity = fields.Float(string="indemnity", required=False)



class HrLoan(models.Model):
    _name = 'hr.loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Loan Request"

    @api.model
    def default_get(self, field_list):
        result = super(HrLoan, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        return result




    name = fields.Char(string="مسمى القرض", readonly=True )
    description =  fields.Char(string="مبرارات القرض", )
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True)
    employee_id = fields.Many2one('hr.employee', string="الموظف", required=True)
    department_id = fields.Many2one('hr.department',
                                    string="الادارة")
    payment_date = fields.Date(string="تاريخ بدء السداد", required=True, default=fields.Date.today())
    loan_amount = fields.Float(string="Loan Amount" ,force_save=True,)
    number = fields.Selection([
        ('1', 'الاول'),
        ('2', 'الثاني'),
        ('3', 'الثالث'),
    ], string="رقم القرض",   )

    state = fields.Selection([
        ('draft', 'مسودة'),
        ('accounting', 'مختص الحساب'),
        ('verfication', 'مسؤول تدقيق المصروفات'),
        ('account_department', 'رئيس الادارة المالية '),
        ('finance_verfifcation', 'المراقب المالي '),
        ('manager', 'الرئيس'),
        ('approved', 'مقبول'),
        ('refuse', 'مرفوضة'),
        ('cancel', 'ملغاة'),
    ], string="State", default='draft', tracking=True, copy=False, )





    @api.onchange('number')
    def loan_amount_onchange(self):
        if self.number:




            if self.employee_id.indemnity == 0 and self.number !="3":
                    message = _('يجب اظافة مكافئة نهاية الخدمة للموظف')
                    mess = {
                        'title': _('تحذير '),
                        'message': message
                    }
                    return {'warning': mess}

            if self.number =="1" or self.number == "2":
                self.loan_amount = self.employee_id.indemnity * 0.8
            else  :
                self.loan_amount = 15000




    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_accounting_approve(self):
        self.write({'state': 'verfication'})

    def action_verification_approve(self):
        self.write({'state': 'account_department'})

    def action_department_approve(self):
        self.write({'state': 'finance_verfifcation'})

    def action_finance_verfifcation_approve(self):
        self.write({'state': 'manager'})


    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_submit(self):
        self.write({'state': 'accounting'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def unlink(self):
        for loan in self:
            if loan.state not in ('draft', 'cancel'):
                raise UserError(
                    'You cannot delete a loan which is not in draft or cancelled state')
        return super(HrLoan, self).unlink()




    @api.model
    def create(self, vals):
                if vals.get('number'):
                    if vals.get('number') == '1' or vals.get('number') == '2':
                        vals['loan_amount'] = 0.8 *  vals.get('employee_id').indemnity * 0.8
                    else :
                        vals['loan_amount'] = 15000

                return super(HrLoan, self).create(vals)


    @api.model
    def button_to_confirm_loan(self):
        states = []
        user = self.env.user
        if user.has_group('ejad_erp_account.group_accounting_employee'):
            states.append('accounting')
        if user.has_group('ejad_erp_account.group_verfication'):
            states.append('verfication')
        if user.has_group('ejad_erp_account.group_finance_verfifcation'):
            states.append('finance_verfifcation')
        if user.has_group('ejad_erp_account.group_department_manager'):
            states.append('account_department')
        if user.has_group('ejad_erp_account.group_finance_verfifcation'):
            states.append('finance_verfifcation')
        if user.has_group('ejad_erp_account.group_university_manager'):
            states.append('manager')

        value = {
            'name': u'‫طلبات  للموافقة',
            'view_type': 'form',
            'view_mode': 'tree,form, graph',
            'res_model': 'hr.loan',
            'type': 'ir.actions.act_window',
            'domain': [('state', 'in', states)],

        }
        return value