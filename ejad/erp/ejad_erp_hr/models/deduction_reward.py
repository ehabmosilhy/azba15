
from odoo import models, fields, api
from odoo.exceptions import except_orm, Warning, RedirectWarning ,ValidationError
from datetime import date, datetime, timedelta
import time
from datetime import time as datetime_time
from dateutil import relativedelta


class hr_deductions_reward(models.Model):

    _name = 'hr.deductions.reward'
    _description = 'Hr Deductions Reward'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'date'

    name = fields.Char(string="الاسم" ,readonly=True)
    date_start = fields.Date(string='التاريخ من', required=True,default=time.strftime('%Y-%m-01'))
    date_end = fields.Date(string='التاريخ الى', required=True,default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    created_by=fields.Many2one('res.users', string="من قام بالانشاء",default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'مسودة'),
        ('close', 'اغلاق'),
    ], string="State", default='draft', copy=False, )
    hr_deduction_ids=fields.One2many('hr.deductions','deduction_reward_id')
    hr_deduction_id=fields.Many2one('hr.deductions')
    date= fields.Date(string="التاريخ الحالى", default= fields.Date.context_today,required=True)

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('hr.deduction.reward')
        return super(hr_deductions_reward, self).create(vals)



    def close_deduction_reward(self):
        return self.write({'state': 'close'})

    #
    # def back_to_draft(self):
    #     return self.write({'state': 'draft'})


    def generate_deduction_reward(self):
        # FIXME SHAIMA should be tested  ('holiday_status_id.is_annual_holiday','=',True) to ('allocation_type', '=', 'accrual'), ('interval_unit', '=', 'years')
        leaves = self.env['hr.leave'].search([('date_to','>=',self.date_start),
                                                 ('date_from','<=',self.date_end),
                                                 ('state','=','validate')
                                                 ])

        if self.hr_deduction_ids:
            for record in self.hr_deduction_ids:
                record.unlink()
        salary_rule_obj = self.env['hr.salary.rule'].search([('name', '=', 'Deductions')])
        deduction_type_obj = self.env['hr.deductions.type'].search([('deduction_type', '=', 'reward')])

        if not deduction_type_obj:
            deduction_type_obj = self.env['hr.deductions.type'].create({
                'name': 'حسمية مكافأت',
                'rule_id': salary_rule_obj.id,
                'deduction_type': 'reward'
            })
        deduction_obj = self.env['hr.deductions']
        if leaves:
            for leave in leaves:
                employee = self.env['hr.leave.allocation'].search([('state', '=', 'validate'),
                                                                    ('holiday_status_id.id', '=',
                                                                     leave.holiday_status_id.id),
                                                                    ('allocation_type', '=', 'accrual'),
                                                                    ('interval_unit', '=', 'years'),
                                                                    ('employee_id.id', '=', leave.employee_id.id),
                                                                    ])
                if employee:
                    d_start = datetime.strptime(str(self.date_start), "%Y-%m-%d").date()
                    d_end = datetime.strptime(str(self.date_end), "%Y-%m-%d").date()
                    date_from = str(leave.date_from)
                    d_from = datetime.strptime(date_from,"%Y-%m-%d %H:%M:%S").date()
                    date_to = str(leave.date_to)
                    d_to = datetime.strptime(date_to,"%Y-%m-%d %H:%M:%S").date()
                    if d_from <= self.date_start and d_to <= self.date_end:
                        no_days = abs((d_to -d_start).days) +1

                    elif d_from >= self.date_start and d_to <= self.date_end:
                        no_days = abs((d_to - d_from).days) + 1

                    elif d_from >= self.date_start and d_to >= self.date_end:
                        no_days = abs((d_end - d_from).days) + 1

                    elif d_from <= self.date_start and d_to >= self.date_end:
                        no_days = abs((d_end - d_start).days) + 1

                    else:
                        pass

                    rec_job= employee.employee_id.job_id
                    #reward_reception_department_perc = (job_id.reward_reception_department * employee.employee_id.contract_id.wage)/100
                    #reward_financial_department_perc = (job_id.reward_financial_department * employee.employee_id.contract_id.wage)/100
                    #reward_security_department_perc= (job_id.reward_security_department * employee.employee_id.contract_id.wage)/100
                    #total=job_id.reward_dean_of_college_center+job_id.reward_deputy_college_center+\
                           #job_id.reward_admin_college_center+job_id.reward_manager_college +\
                           #job_id.reward_government_relation +job_id.reward_calling +\
                           #job_id.reward_passport_representative_external +\
                           #job_id.reward_passport_representative_internal + \
                           #job_id.reward_purchase_representative+ job_id.reward_revenue_collector+job_id.other_reward+\
                           #reward_reception_department_perc+reward_financial_department_perc+reward_security_department_perc
                    total = 0.00
                    wage = 0.00
                    salary_rule_obj = self.env['hr.salary.rule'].search([('name', '=', 'Deductions')])
                    deduction_reward_type_ids = self.env['hr.deductions.type'].search([('deduction_type', '=', 'reward')])
                    wage = employee.employee_id.contract_id.wage or 0.00
                    if not employee.employee_id.contract_id.is_exceptional:
                        for deduction_type in deduction_reward_type_ids:
                            total = 0.00
                            if deduction_type.reward_dean_of_college_center and rec_job.reward_dean_of_college_center:
                                total += rec_job.reward_dean_of_college_center
                            if deduction_type.reward_deputy_college_center and rec_job.reward_deputy_college_center:
                                total += rec_job.reward_deputy_college_center
                            if deduction_type.reward_admin_college_center and rec_job.reward_admin_college_center:
                                total += rec_job.reward_admin_college_center
                            if deduction_type.reward_manager_college and rec_job.reward_manager_college:
                                total += rec_job.reward_manager_college
                            if deduction_type.reward_security_department and rec_job.reward_security_department:
                                total += rec_job.reward_security_department  * (wage / 100.00)
                            if deduction_type.reward_reception_department and rec_job.reward_reception_department:
                                total += rec_job.reward_reception_department  * (wage / 100.00)
                            if deduction_type.reward_financial_department and rec_job.reward_financial_department:
                                total += rec_job.reward_financial_department  * (wage / 100.00)
                            if deduction_type.reward_government_relation and rec_job.reward_government_relation:
                                total += rec_job.reward_government_relation
                            if deduction_type.reward_calling and rec_job.reward_calling:
                                total += rec_job.reward_calling
                            if deduction_type.reward_passport_representative_external and rec_job.reward_passport_representative_external:
                                total += rec_job.reward_passport_representative_external
                            if deduction_type.reward_passport_representative_internal and rec_job.reward_passport_representative_internal:
                                total += rec_job.reward_passport_representative_internal
                            if deduction_type.reward_purchase_representative and rec_job.reward_purchase_representative:
                                total += rec_job.reward_purchase_representative
                            if deduction_type.reward_purchase_representative and rec_job.reward_purchase_representative:
                                total += rec_job.reward_purchase_representative
                            if deduction_type.reward_revenue_collector and rec_job.reward_revenue_collector:
                                total += rec_job.reward_revenue_collector
                            if deduction_type.other_reward and rec_job.other_reward:
                                total += rec_job.other_reward
                            if deduction_type.food_reward and rec_job.food_reward:
                                total += rec_job.food_reward

                            one_day_cost = (total / 30)
                            amount = one_day_cost * no_days
                            # amount = one_day_cost * no_day

                            if amount:
                                vals = {
                                    'employee_id': employee.employee_id.id,
                                    'type_id': deduction_type.id,
                                    'amount': amount,
                                    'de_amount': amount,
                                    'deduction_reward_id': self.id,
                                    'date_deducted': self.date_start,
                                }
                                deduction_obj.create(vals)

